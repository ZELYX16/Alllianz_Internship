data_1: list[int|str] = [1,2,3,"x","k","i"]
data_2 = [5,6,7]

data_1.append("t")
print(f'Append to list : {data_1}')

cp  = data_1.copy()
print(f'copy list : {cp}')

count = data_1.count(3)
print(f'count of an element in list : {count}')

data_1.extend(data_2)
print(f'extended list : {data_1}')

idx = data_1.index("k")
print(f'index of an element in list : {idx}')

data_1.insert(3,4)
print(f'element inserted at index 3 in list : {data_1}')

data_1.remove("k")
print(f'Removed k from the list : {data_1}')

data_1.reverse()
print(f'Reversed the list : {data_1}')

import tiktoken
from Data import ENCODING_MAP

for key in ENCODING_MAP.keys():
    print(f"Model : {key} : {tiktoken.encoding_for_model(key)}")