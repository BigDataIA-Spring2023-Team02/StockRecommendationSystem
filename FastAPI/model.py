import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import DistilBertModel, DistilBertTokenizer, DistilBertConfig, PreTrainedModel
from transformers import Trainer, TrainingArguments
from torch.utils.data import Dataset
import torch
import torch.nn as nn
import joblib
from transformers import AdamW, get_linear_schedule_with_warmup
import pandas as pd
import pickle
from transformers import DistilBertTokenizer
from torch.utils.data import Dataset
import torch
from sklearn.model_selection import train_test_split
import sklearn
from transformers import DistilBertPreTrainedModel, DistilBertModel

# Convert the data into text format
def data_to_text(data):
    text_data = data.apply(lambda x: f"Symbol: {x['symbol']} Daily Return: {x['daily_return']} Sentiment: {x['sentiment']}", axis=1)
    return text_data.tolist()

class CustomDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx], dtype=torch.float).unsqueeze(0) # Convert labels to float
        return item

    def __len__(self):
        return len(self.encodings.input_ids)

#Custom DistilBertForSequenceRegression model
class DistilBertForSequenceRegression(DistilBertPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels

        self.distilbert = DistilBertModel(config)
        self.pre_classifier = nn.Linear(config.dim, config.dim)
        self.classifier = nn.Linear(config.dim, self.config.num_labels)
        self.dropout = nn.Dropout(config.seq_classif_dropout)

        self.init_weights()

    def forward(
        self,
        input_ids=None,
        attention_mask=None,
        head_mask=None,
        inputs_embeds=None,
        labels=None,
    ):
        outputs = self.distilbert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
        )

        hidden_state = outputs[0]  # (bs, seq_len, dim)
        pooled_output = hidden_state[:, 0]  # (bs, dim)
        pooled_output = self.pre_classifier(pooled_output)  # (bs, dim)
        pooled_output = nn.ReLU()(pooled_output)  # (bs, dim)
        pooled_output = self.dropout(pooled_output)  # (bs, dim)
        logits = self.classifier(pooled_output)  # (bs, num_labels)

        outputs = (logits,) + outputs[1:]  # add hidden states and attention if they are here

        if labels is not None:
            loss_fct = nn.MSELoss()
            loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1, self.num_labels))
            outputs = (loss,) + outputs

        return outputs

class CustomPredictionDataset(Dataset):
    def __init__(self, encodings):
        self.encodings = encodings

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        return item

    def __len__(self):
        return len(self.encodings.input_ids)
    



# Load and prepare the dataset
data = pd.read_csv('/Users/ajinabraham/Documents/BigData7245/BigData/FastAPI/merged_data.csv')
train_data, val_data = train_test_split(data, test_size=0.2, random_state=42)


# Convert data to text
train_text = data_to_text(train_data)
val_text = data_to_text(val_data)

# Tokenize and preprocess the data
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")
train_encodings = tokenizer(train_text, padding=True, truncation=True, return_tensors='pt')
val_encodings = tokenizer(val_text, padding=True, truncation=True, return_tensors='pt')

# Extract labels
train_labels = train_data["next_week_return"].values
val_labels = val_data["next_week_return"].values

# Create dataset objects
train_dataset = CustomDataset(train_encodings, train_labels)
val_dataset = CustomDataset(val_encodings, val_labels)

# Create the model
config = DistilBertConfig.from_pretrained("distilbert-base-uncased", num_labels=1)
model = DistilBertForSequenceRegression.from_pretrained("distilbert-base-uncased", config=config)

# Train the model
training_args = TrainingArguments(
    output_dir="output",
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    num_train_epochs=5,  # increased number of epochs
    evaluation_strategy="epoch",  # evaluate at the end of each epoch
    save_strategy="epoch",  # save the model at the end of each epoch
    load_best_model_at_end=True,  # load the best model at the end of training
    metric_for_best_model="eval_loss",  # use validation loss to determine the best model
    greater_is_better=False,  # lower validation loss is better
)

# Custom optimizer and scheduler
num_training_steps = len(train_dataset) // training_args.per_device_train_batch_size * training_args.num_train_epochs
optimizer = AdamW(model.parameters(), lr=5e-5)
scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(0.1 * num_training_steps), num_training_steps=num_training_steps)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    optimizers=(optimizer, scheduler),
)

trainer.train()

# Save the fine-tuned model
with open("fine_tuned_model.pkl", "wb") as f:
    pickle.dump(model, f)
# Save the trained model
torch.save(model.state_dict(), "model.pt")





# Load the saved model
with open("fine_tuned_model.pkl", "rb") as f:
    model = pickle.load(f)


# Load the tokenizer
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

# Load and prepare the dataset
data = pd.read_csv('/Users/ajinabraham/Documents/BigData7245/BigData/FastAPI/merged_data.csv')

# Convert data to text
text_data = data_to_text(data)

# Tokenize and preprocess the data
encodings = tokenizer(text_data, padding=True, truncation=True, return_tensors='pt')

# Create dataset object
dataset = CustomPredictionDataset(encodings)


# Predict next week returns using the saved model
with torch.no_grad():
    model.eval()
    outputs = model(**encodings)
    predictions = outputs[0].detach().numpy()

# Create a DataFrame with stock symbols and their predicted next week returns
symbols = data['symbol'].values
predicted_returns = pd.DataFrame({'symbol': symbols, 'predicted_return': predictions.flatten()})

# Sort the stocks by predicted return in descending order and select the top 5
top_5_stocks = predicted_returns.sort_values(by='predicted_return', ascending=False).head(5)

print("Top 5 stocks:")
print(top_5_stocks)