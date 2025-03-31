import random
counter = 0
rand_list = []
while counter < 10:
    random_number = random.randint(1, 20)
    if random_number not in rand_list:
        rand_list.append(random_number)
    counter += 1

print(rand_list)

list_comprehension_below_10 = [x for x in rand_list if x < 10]
print(list_comprehension_below_10)

list_comprehension_below_10_filter = list(filter(lambda x: x < 10, rand_list))
print(list_comprehension_below_10_filter)

