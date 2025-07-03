## How does panasonic updating of state works?

- When we send the first state update command, we will receive an operation_token back
- Each subsequent request needs to also include this operation_token
- If no operation_token is included, there will be a lock on the aircon for 2 minutes, so only the device that started the operation can edit it during this time
- We need to keep track of this operation token
