# cascade
[GameNGen](https://arxiv.org/abs/2408.14837) applied to falling sands.

Falling Sand implementation taken from https://github.com/Antiochian/Falling-Sand/tree/master

## Rough Plan:

- [ ] Implement falling sands such that:
    - [x] It can be played and the physics behaviour can be verified
    - [ ] It can be run in 'simulation' mode whereby an arbitrary number of game instances can be computer controlled at once and have their frames recorded
        - [x] simulation renderer
        - [ ] simulation input handler
            - [x] enacting of pen strokes 
            - [ ] saving actions
            - [ ] generating pen strokes
            - [ ] bezier curve pen strokes and speed functions
        - [ ] proper sim initialization and multi processing 
    - [ ] The backend can be swapped for a model that sends rending instructions to pygame
- [ ] Construct a dataset
- [ ] Construct a model
    - [ ] temporal [VAR?](https://arxiv.org/pdf/2404.02905)
