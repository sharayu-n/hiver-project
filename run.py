from src.build_dataset import build_dataset, save_dataset
from src.generate import run_generation
from src.evaluate import evaluate


def main():
    rows = build_dataset()
    save_dataset(rows)
    run_generation()
    evaluate()


if __name__ == "__main__":
    main()