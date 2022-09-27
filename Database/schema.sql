#Create super neighborhoods table
CREATE TABLE houston_super_neighborhoods (

id INT PRIMARY KEY NOT NULL,

name TEXT,

total_population varchar,

median_household_income varchar 
);



#add new properties table

CREATE TABLE properties (

id INT PRIMARY KEY NOT NULL,
	
super_id int,

address TEXT,

price MONEY,

type text,

bed int,

sqft int,

walk int,

transit int,

bike int,
	
zipcode int,

FOREIGN KEY (super_id) REFERENCES houston_super_neighborhoods (id)
);

# Possibly needed queries
select *
from houston_super_neighborhoods


#delete all rows from table
Delete From houston_super_neighborhoods

#drop table if needed
DROP TABLE properties

# Select statment that Joins both tables
Select p.id, p.super_id,  h.name, h.total_population, h.median_household_income, p.address, p.price, p.type, p.bed, p.sqft, p.walk, p.transit, p.bike, p.zipcode
from properties as p inner join houston_super_neighborhoods as h
on p.super_id = h.id
order by p.price asc


#create new table using select statment
create table super_properties as
Select p.id, p.super_id,  h.name, h.total_population, h.median_household_income, p.address, p.price, p.type, p.bed, p.sqft, p.walk, p.transit, p.bike, p.zipcode
from properties as p inner join houston_super_neighborhoods as h
on p.super_id = h.id
