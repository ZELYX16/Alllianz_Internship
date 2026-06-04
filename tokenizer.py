import argparse
import tiktoken



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("--cost",default = 2.5, type=float)
    args = parser.parse_args()

    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = 0

    try:
        with open(args.filename,"r") as f:
            content = f.read()
            tokens = encoding.encode(content)
            num_tokens += len(tokens)
        print("---Tokenizer---")
        print("Number of tokens: ", num_tokens)
        print("Input Token rate / Million : ",args.cost)
        print(f'Cost: $, {((num_tokens/1000000)*args.cost):.6f}')

    except FileNotFoundError:
        print("The file doesnt exists")
    
    
if __name__ == "__main__":
    main()