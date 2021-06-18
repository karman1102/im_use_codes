# for employee allocation of tickets
employee = ['emp' + str(s) for s in list(range(1, 7))]
tickets = ['ticket' + str(s) for s in list(range(1, 50))]

employee_balance = 5
ticket_allocation = {}
# check for total number of tickets

# bucket bifurcation on the basis of which column?
total_employee_balance = 100
while tickets and total_employee_balance:
    i: str
    for emp in employee:
        #     employee_balance = limit(40)-assigned/incomplete(2) OR completed tickets = 38
        #     fetch from tickets count of tickets closed from db
        # if balance[emp]:
            if emp in ticket_allocation:
                # checks if key for current employee exists in dictionary
                ticket_allocation[emp].append(tickets[-1])
            else:
                ticket_allocation[emp] = [tickets[-1]]
            #  remove the allocated ticket/change flag of allocated ticket by writing a query
            tickets.pop(-1)
            total_employee_balance-=1
            if not tickets or not employee_balance:
                break
        # else:
        #     continue

print(ticket_allocation)
