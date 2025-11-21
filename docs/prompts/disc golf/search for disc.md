#Search for disc

A user should be able to check if his disc can be found in the system.

Create a new page which allows the user to upload a disc.

If one or more matches are found, show the top 3 matches (ranked in descending order with best match first), similarly to how discs are shown on the front page.



##Tasks:

###Frontend

- route: /discs/search
- page file: pages/SearchDisc.tsx


###Backend

- route: /discs/identification/search
    - this route already exists. Use it and make necessary changes if needed