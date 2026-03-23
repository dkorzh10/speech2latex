
import pandas as pd
import json
import os
import torchaudio   
from sklearn.model_selection import train_test_split

BASE_PATH = "/mnt/shared_ru.ml.SZ-2_000049/antispoofing_datasets/S2L_full_dataset/"
MAX_LEN = 300
NEG_PATH = "/mnt/shared_ru.ml.SZ-2_000049/antispoofing_datasets/cv-corpus-21.0-2025-03-14/en/clips"

df_eq_train = pd.read_csv(os.path.join(BASE_PATH, "equations_train.csv"))
df_eq_test = pd.read_csv(os.path.join(BASE_PATH, "equations_test.csv"))
df_sent_train = pd.read_csv(os.path.join(BASE_PATH, "sentences_train.csv"))
df_sent_test = pd.read_csv(os.path.join(BASE_PATH, "sentences_test.csv"))
df_mb = pd.read_csv(os.path.join(BASE_PATH, "equations_mathbridge_clean.csv"))

df_eq_train["audio_path"] = df_eq_train["audio_path"].apply(lambda x: os.path.join(BASE_PATH, x))
df_eq_test["audio_path"] = df_eq_test["audio_path"].apply(lambda x: os.path.join(BASE_PATH, x))
df_sent_train["audio_path"] = df_sent_train["audio_path"].apply(lambda x: os.path.join(BASE_PATH, x))
df_sent_test["audio_path"] = df_sent_test["audio_path"].apply(lambda x: os.path.join(BASE_PATH, x))
df_mb["audio_path"] = df_mb["audio_path"].apply(lambda x: os.path.join(BASE_PATH, x))


df_neg = pd.read_csv("/mnt/shared_ru.ml.SZ-2_000049/antispoofing_datasets/cv-corpus-21.0-2025-03-14/en/validated.tsv", sep="\t")
df_neg["audio_path"] = df_neg["path"].apply(lambda x: os.path.join(NEG_PATH, x))
df_neg["sentence_normalized"] = df_neg["sentence"].apply(lambda x: f"{str(x).lower()}")
df_neg = df_neg.sample(10000, random_state=42).reset_index(drop=True)
# x, sr = torchaudio.load(df_neg["audio_path"].iloc[0])
# print(x.shape, sr)

print(df_eq_train.shape, df_eq_test.shape, df_sent_train.shape, df_sent_test.shape, df_mb.shape, df_neg.shape)


df_eq_train["sentence_normalized"] = df_eq_train["sentence_normalized"].apply(lambda x: f"${str(x)}$")
df_eq_test["sentence_normalized"] = df_eq_test["sentence_normalized"].apply(lambda x: f"${str(x)}$")
# df_mb["sentence_normalized"] = df_mb["sentence_normalized"].apply(lambda x: f"${str(x)}$")

df_train = pd.concat([df_eq_train, df_sent_train, df_mb])  # , df_neg needs to be resampled 
df_test = pd.concat([df_eq_test, df_sent_test])
df_train = df_train[df_train["sentence_normalized"].apply(lambda x: len(x)) <= MAX_LEN]
df_test = df_test[df_test["sentence_normalized"].apply(lambda x: len(x)) <= MAX_LEN]

# for demo to use all train data during training
df_val = df_test.sample(frac=0.2, random_state=42).reset_index(drop=True)

# train_idx, val_idx = train_test_split(df_train.index, test_size=0.2, random_state=42)
# df_train = df_train.iloc[train_idx]
# df_val = df_train.iloc[val_idx]
# df_train = df_train.reset_index(drop=True)
# df_val = df_val.reset_index(drop=True)

print(df_train["sentence_normalized"].apply(lambda x: len(x)).max())
print(df_val["sentence_normalized"].apply(lambda x: len(x)).max())
print(df_test["sentence_normalized"].apply(lambda x: len(x)).max())



def write(path, dict):
    with open(path, "w+") as f:
        f.write(json.dumps(dict,indent=4))

train_anno = {
    "annotation":[ {"path":row['audio_path'], "text":row['sentence_normalized'], "task" : "asr" } for _, row in df_train.iterrows()]
}

val_anno = {
    "annotation":[ {"path":row['audio_path'], "text":row['sentence_normalized'], "task" : "asr" } for _, row in df_val.iterrows()]
}

test_anno = {
    "annotation":[ {"path":row['audio_path'], "text":row['sentence_normalized'], "task" : "asr" } for _, row in df_test.iterrows()]
}


write("metadata/train_anno.json", train_anno)
write("metadata/val_anno.json", val_anno)
write("metadata/test_anno.json", test_anno)

# df = pd.read_csv("train.csv")
# test_df = df[df["language"] == "eng"]

# def write( path,dict):
#     with open(path, "w+") as f:
#         f.write(json.dumps(dict,indent=4))

# test_anno = {
#     "annotation":[ {"path":row['audio_path'], "text":row['formula_normalized'], "task" : "asr" } for _, row in test_df.iterrows()]
# }

# write("data/test_anno.json",test_anno)
