import argparse
import tiktoken
from Data import ENCODING_MAP,PRICE_MAP,fetch_realtime_pricing


def main():

    active_prices = PRICE_MAP.copy()
    #Import data from Data.py 
    live_price_data = fetch_realtime_pricing(ENCODING_MAP.keys())

    if live_price_data:
        # Merge live updates into baseline map
        active_prices.update(live_price_data)
        print("\n* Live pricing updated successfully from OpenRouter API.")
    else:
        print("Running with default offline pricing schema.")

    #Parse the filename from argument
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    
    num_tokens = 0
    
    #Read the file content 
    try:
        with open(args.filename, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{args.filename}' doesn't exist.")
        exit(1)
    except Exception as err:
        print(f"Error reading file: {err}")
        exit(1)
    try:

        #Interactive CLI loop 
        while True:
            print("\nSelect your Model: [Exit : 0 ]\n")

            #converting the keys(models) in the object into a list
            models = list(ENCODING_MAP.keys())

            for index, model in enumerate(
                models,
                start=1
            ):
                print(f"{index}. {model}")


            try:
                selection = int(input("\nEnter choice: "))
            except ValueError:
                print("\nInvalid input! Please enter a valid number.\n")
                continue

            if selection == 0:
                print("CLI Tool Exited !!!")
                exit(0)

            elif selection < 1 or selection > len(ENCODING_MAP):
                print("\nInvalid selection!\n")
                continue

            selected_model = models[
                selection - 1
            ]
            
            #Calculations 
            encoding = tiktoken.encoding_for_model(selected_model)
            tokens = encoding.encode(content)
            num_tokens = len(tokens)
            total_cost = active_prices[selected_model]["input"] * num_tokens
            
            #Output
            print("\n-----------------------------------")
            print("CLI Tokenizer - Execution Report")
            print("-----------------------------------")
            print("Model Selected : ",selected_model)
            print("Number of Tokens  : ",num_tokens)
            print(f"Estimated Input Token cost : {(total_cost):.8f} \n")
            print("-------------------------------------")

            
        
    except FileNotFoundError:
        print("Error : The file doesn't exist.")
    
    except Exception as err:
        print("Error : ", err)
    
    
if __name__ == "__main__":
    main()