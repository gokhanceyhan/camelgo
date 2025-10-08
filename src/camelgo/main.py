import argparse
import random

def main():
    parser = argparse.ArgumentParser(description="Return a random number.")
    parser.add_argument('--min', type=int, default=0, help='Minimum value (inclusive)')
    parser.add_argument('--max', type=int, default=100, help='Maximum value (inclusive)')
    args = parser.parse_args()

    number = random.randint(args.min, args.max)
    print(f"Random number between {args.min} and {args.max}: {number}")

if __name__ == "__main__":
    main()