import pandas as pd
import os

""" SIMPLE CSV DATABASE MANIPULATIONS FOR ANNOUNCMENTS """


def add_new_user(id):

    if id not in get_users():

        df = pd.read_csv(os.path.join("app/database/csv", "users.csv"))

        df = df.concat([df, pd.DataFrame({"user": [id]})], ignore_index=True)

        df.to_csv(os.path.join("app/database/csv", "users.csv"), index=False)


def get_users():
    return pd.read_csv(os.path.join("app/database/csv", "users.csv"))["user"].tolist()


def delete_user(id):
    df = pd.read_csv(os.path.join("app/database/csv", "users.csv"))
    df = df[df["user"] != id]
    df.to_csv(os.path.join("app/database/csv", "users.csv"), index=False)
