name = "Sunil"
print(f"Hello, {name}!")

color = input("Enter your favorite color: ")
if color == 'Green' or color == 'green':
    print("Your favorite color is Green.")
else:
    print("Your favorite color is not Green.")

a=5
b=10




def sum(a, b):
    return a + b
c=sum(a,b)
print(f"The sum of {a} and {b} is {c}.")

def timess(a, b):
    return a * b

d=timess(a,b)
print(f"The product of {a} and {b} is {d}.")


# switch case example:
option = input("Enter an option (add/multiply): ")
match option:
    case "add":
        print(f"The sum of {a} and {b} is {c}.")
    case "multiply":
        print(f"The product of {a} and {b} is {d}.")
    case _:
        print("Invalid option.")



list_example = [1, 2, 3, 4, 5]
print(f"The list example is: {list_example}")

# dictionary example meaning key-value pairs
dict_example = {"name": "Sunil", "age": 25}
print(f"The dictionary example is: {dict_example}")

# set example meaning a collection of unique elements
set_example = {1, 2, 3, 4, 5,5}
print(f"The set example is: {set_example}")

# tuple example meaning an ordered collection of elements
tuple_example = (6,1, 2, 3, 4, 5)
print(f"The tuple example is: {tuple_example}")

