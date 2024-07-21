import pandas as pd
import os

""" SIMPLE CSV DATABASE MANIPULATIONS """


def add_new_user(id):

    if id not in get_users():

        df = pd.read_csv(os.path.join("app/admin/stats/csv", "users.csv"))

        df = df._append(pd.DataFrame({"user": [id],
                                      "looping": [0],
                                      "all_zones": [0]}), ignore_index=True)

        df.to_csv(os.path.join("app/admin/stats/csv", "users.csv"), index=False)


def get_users():
    return pd.read_csv(os.path.join("app/admin/stats/csv", "users.csv"))["user"].tolist()


def delete_user(id):
    df = pd.read_csv(os.path.join("app/admin/stats/csv", "users.csv"))
    df = df[df["user"] != id]
    df.to_csv(os.path.join("app/admin/stats/csv", "users.csv"), index=False)



# SWITCHES FOR STATS DATA

def off_looping(id):
    df = pd.read_csv(os.path.join("app/admin/stats/csv", "users.csv"))
    if df.loc[df["user"] == id, "looping"].item() == 1:
        df.loc[df["user"] == id, "looping"] = 0
        df.to_csv(os.path.join("app/admin/stats/csv", "users.csv"), index=False)

def on_looping(id):
    df = pd.read_csv(os.path.join("app/admin/stats/csv", "users.csv"))
    if df.loc[df["user"] == id, "looping"].item() == 0:
        df.loc[df["user"] == id, "looping"] = 1
        df.to_csv(os.path.join("app/admin/stats/csv", "users.csv"), index=False)

def off_all_zones(id):
    df = pd.read_csv(os.path.join("app/admin/stats/csv", "users.csv"))
    if df.loc[df["user"] == id, "all_zones"].item() == 1:
        df.loc[df["user"] == id, "all_zones"] = 0
        df.to_csv(os.path.join("app/admin/stats/csv", "users.csv"), index=False)

def on_all_zones(id):
    df = pd.read_csv(os.path.join("app/admin/stats/csv", "users.csv"))
    if df.loc[df["user"] == id, "all_zones"].item() == 0:
        df.loc[df["user"] == id, "all_zones"] = 1
        df.to_csv(os.path.join("app/admin/stats/csv", "users.csv"), index=False)

def get_looping(id):
    df = pd.read_csv(os.path.join("app/admin/stats/csv", "users.csv"))
    return df.loc[df["user"] == id, "looping"].item()

def get_all_zones(id):
    df = pd.read_csv(os.path.join("app/admin/stats/csv", "users.csv"))
    return df.loc[df["user"] == id, "all_zones"].item()


# STATS FOR PANEL
def get_stats():
    df = pd.read_csv(os.path.join("app/admin/stats/csv", "users.csv"))
    return df["looping"].sum(), df["all_zones"].sum()
