from batch_processing.batch_method import send_batch
from file_handling import csv_handling
from live_processing import live_method


def main():
    selection = input("Batch or live? (b/l): ")
    if selection.lower() == "b":
        batch = send_batch()

    if selection.lower() == "l":
        live_method.send_live_call()


