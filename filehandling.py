
while(1):

    try:
        action = int(input('''
            1.Read file
            2.Write file
            3.Append file
            4.Exit
    '''))
        if action == 4:
            break
        if action not in [1,2,3]:
            print("Invalid selection !!!")
            continue
        file_name = input("Enter your file name : ")
        options = ["r","w","a"]

        with open(file_name,options[action - 1]) as f:
            if action == 1:
                print(f.read())
            elif action == 2:
                data = input("Enter the data :")
                f.write(data)
                print("Data written successfully !!!")
            elif action == 3:
                data = input("Enter the data :")
                f.write(data)
                print("Data appended successfully !!!")

    except ValueError:
        print("Error : Invalid Value(type) Enterd .")

    except FileNotFoundError:
        print("Error : File not found .")


    

