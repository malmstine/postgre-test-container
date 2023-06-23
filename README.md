# Postgre Test Container

Module to create postgre test container from docker image


## Requirements
* docker on host

## Example
```
with temporary_postgres() as cp:
    # connect(port=cp.port, user=cp.user, db=cp.db, password=cp.passwrod) 
```