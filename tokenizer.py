import argparse
import tiktoken



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("--cost",default = 2.5/1000000, type=float)
    args = parser.parse_args()

    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = 0

    with open(args.filename,"r") as f:
        content = f.read()
        tokens = encoding.encode(content)
        num_tokens += len(tokens)
    
    print("Number of tokens: ", num_tokens)
    print("Cost: $", num_tokens * args.cost)

if __name__ == "__main__":
    main()