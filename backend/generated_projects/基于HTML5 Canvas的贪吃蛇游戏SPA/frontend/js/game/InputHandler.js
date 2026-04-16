class InputHandler {
    constructor(gameController) {
        this.gameController = gameController;
        this.currentDirection = 'RIGHT';
        this.nextDirection = 'RIGHT';
        this.keyState = {};
        this.keyMap = {
            'ArrowUp': 'UP',
            'ArrowDown': 'DOWN',
            'ArrowLeft': 'LEFT',
            'ArrowRight': 'RIGHT',
            'KeyW': 'UP',
            'KeyS': 'DOWN',
            'KeyA': 'LEFT',
            'KeyD': 'RIGHT'
        };
        this.oppositeDirections = {
            'UP': 'DOWN',
            'DOWN': 'UP',
            'LEFT': 'RIGHT',
            'RIGHT': 'LEFT'
        };
        this.init();
    }

    init() {
        document.addEventListener('keydown', (event) => this.handleKeyDown(event));
        document.addEventListener('keyup', (event) => this.handleKeyUp(event));
    }

    handleKeyDown(event) {
        const key = event.code;
        if (this.keyMap[key]) {
            event.preventDefault();
            this.keyState[key] = true;
            this.processDirection();
        }
        if (key === 'Space') {
            event.preventDefault();
            this.gameController.togglePause();
        }
        if (key === 'Enter' && this.gameController.isGameOver) {
            event.preventDefault();
            this.gameController.resetGame();
        }
    }

    handleKeyUp(event) {
        const key = event.code;
        if (this.keyMap[key]) {
            this.keyState[key] = false;
        }
    }

    processDirection() {
        let newDirection = null;
        for (const [key, direction] of Object.entries(this.keyMap)) {
            if (this.keyState[key]) {
                newDirection = direction;
                break;
            }
        }
        if (newDirection && newDirection !== this.oppositeDirections[this.currentDirection]) {
            this.nextDirection = newDirection;
        }
    }

    update() {
        if (this.nextDirection !== this.currentDirection) {
            this.currentDirection = this.nextDirection;
            return this.currentDirection;
        }
        return null;
    }

    getDirection() {
        return this.currentDirection;
    }

    reset() {
        this.currentDirection = 'RIGHT';
        this.nextDirection = 'RIGHT';
        this.keyState = {};
    }
}

export default InputHandler;