import time

def get_date():
    return time.strftime("%Y:%j:%H:%M")

d = get_date()

print(d)
t = time.strptime(d, "%Y:%j:%H:%M")
print(t, dir(t))
print(time.strptime)