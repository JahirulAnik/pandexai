import random

random.seed(42)

regions = ["North", "south", "East", "west", "North", "South"]
genders = ["M", "Male", "F", "Female", "f", "male"]
statuses = ["active", "Active", "inactive", "Inactive"]
date_formats = ["2024-{:02d}-{:02d}", "{:02d}/{:02d}/2024", "{}-{}-2024"]
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]

def random_date():
    fmt = random.choice(date_formats)
    d = random.randint(1, 28)
    m = random.randint(1, 6)
    if fmt == "{}-{}-2024":
        return f"{d}-{months[m-1]}-2024"
    return fmt.format(m, d)

rows = []
rows.append("customer_id,name,region,amount,signup_date,gender,status")

names = ["John Smith", "jane doe", "Bob Lee", "alice brown", "Mike Ross",
         "Sara Khan", "Tom Hill", "Nina Roy", "David Kim", "Emma Watts",
         "Chris Park", "Laura Diaz", "Omar Ali", "Grace Chen", "Leo Fox"]

cid = 1
while len(rows) < 101:
    name = random.choice(names)
    region = random.choice(regions)
    amount = round(random.uniform(50, 500), 2)
    date = random_date()
    gender = random.choice(genders)
    status = random.choice(statuses)

    roll = random.random()
    if roll < 0.06:
        # completely empty row (id only)
        rows.append(f"{cid},,,,,,")
    elif roll < 0.14:
        # missing a couple fields, using blank-like placeholders
        placeholder = random.choice(["", "N/A", "-", "null"])
        rows.append(f"{cid},{name},{region},{placeholder},{placeholder},{gender},{status}")
    elif roll < 0.20 and len(rows) > 5:
        # exact duplicate of the previous row
        rows.append(rows[-1])
    elif roll < 0.28:
        # conflicting duplicate: same id as previous customer, different data
        prev_id = cid - 1 if cid > 1 else cid
        alt_gender = random.choice(genders)
        alt_amount = round(random.uniform(50, 500), 2)
        rows.append(f"{prev_id},{name},{region},{alt_amount},{date},{alt_gender},{status}")
    else:
        rows.append(f"{cid},{name},{region},{amount},{date},{gender},{status}")

    cid += 1

with open("large_test.csv", "w", encoding="ascii", newline="") as f:
    f.write("\n".join(rows[:101]) + "\n")

print(f"Wrote {len(rows[:101]) - 1} data rows to large_test.csv")
