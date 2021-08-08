import random 
import pandas as pd
import numpy as np
from faker import Faker


mx=pd.read_csv('mx.csv')
mx=mx.set_index('before')

class Customer:
    """
    a single customer that moves through the supermarket in a MCMC simulation. """
    
    def __init__(self, id):
        self.id=id
    #    self.name = name
        self.location='entrance'
        self.transition_probs=mx

    def __repr__(self):
        return f'Customer {self.name} (id {self.id}) is in {self.location}'
    
    def next_state(self):
        ''' Propagates the customer to the next state. Returns nothing.   '''
        self.location = np.random.choice(self.transition_probs.columns.values, p=self.transition_probs.loc[self.location])
    @property
    def is_active(self):
        """ Returns True if the customer has not reached the checkout yet. """
        if self.location!='checkout':
            return True
        else:
            return False


SIMULATE_MINUTES = 15
NEW_CUSTOMERS_PER_MINUTE = 1.6  # lambda of poisson distribution


class Supermarket:
    """manages multiple Customer instances that are currently in the market.    """
    
    def __init__(self):
        # a list of Customer objects
        self.customers = []
        self.minutes = 0
        self.last_id = 0
        self.list = pd.DataFrame(columns=['timestamp', 'customer_id', 'name','location'])
        
    def __repr__(self):
    
        return f"{self.get_time}"
    @property

    def get_time(self):
        hour = 7 + self.minutes // 60
        min = self.minutes % 60
        return f"{hour:02}:{min:02}:00"

    def print_customers(self):
        """print all customers with the current time and id in CSV format.
        """
        for customer in self.customers:
            timestamp = self.get_time
            customer_name = customer.name
            customer_id = customer.id
            location = customer.location
            self.list=self.list.append({'timestamp' : timestamp, 'name' : customer_name, 'customer_id' : customer_id, 'location' : location}, ignore_index=True)

    def next_minute(self): #control our customers
        """propagates all customers to the next state."""
        self.minutes += 1
        for shopper in self.customers:
            shopper.next_state()
            self.print_row(shopper)
        
    def add_new_customers(self): #create a customer
        """randomly creates new customers."""
        n = np.random.poisson(NEW_CUSTOMERS_PER_MINUTE)
        for i in range(n):
            name = Faker().name()
            id = self.last_id
            shopper=Customer(id, name)
            self.customers.append(shopper) #this function in my supermarket object literally creates other objects
            self.last_id += 1
            self.print_row(shopper)
    
    def remove_exitsting_customers(self):
        """removes every customer that is not active any more.
        """
        self.customers = [i for i in self.customers if i.is_active]
        
    def print_row(self, customer):
        """prints one row of CSV"""
        row = str(self) + ", " + str(customer)
        print(row)
   
if __name__ == "__main__":
    s = Supermarket()
    for i in range(SIMULATE_MINUTES):
        s.next_minute()
        s.add_new_customers()
        s.print_customers()
        s.remove_exitsting_customers()
    s.list.to_csv('day.csv')





