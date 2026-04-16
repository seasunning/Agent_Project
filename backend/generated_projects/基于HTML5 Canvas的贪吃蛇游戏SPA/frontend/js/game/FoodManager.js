class FoodManager {
    constructor(config) {
        this.config = config;
        this.food = {
            position: { x: 0, y: 0 }
        };
        this.gridSize = config.gridSize;
        this.canvasWidth = config.canvasWidth;
        this.canvasHeight = config.canvasHeight;
        this.generateFood();
    }

    /**
     * 生成新的食物位置
     * 确保食物不会生成在蛇的身体上（需要外部传入蛇的身体坐标）
     * @param {Array} snakeBody - 蛇的身体坐标数组
     */
    generateFood(snakeBody = []) {
        let newFoodPosition;
        let isOnSnake;
        
        do {
            // 计算网格坐标（确保食物在网格上对齐）
            const maxX = Math.floor(this.canvasWidth / this.gridSize) - 1;
            const maxY = Math.floor(this.canvasHeight / this.gridSize) - 1;
            
            const gridX = Math.floor(Math.random() * maxX);
            const gridY = Math.floor(Math.random() * maxY);
            
            newFoodPosition = {
                x: gridX * this.gridSize,
                y: gridY * this.gridSize
            };
            
            // 检查新食物是否在蛇的身体上
            isOnSnake = snakeBody.some(segment => 
                segment.x === newFoodPosition.x && segment.y === newFoodPosition.y
            );
            
        } while (isOnSnake);
        
        this.food.position = newFoodPosition;
    }

    /**
     * 检测蛇头是否与食物碰撞
     * @param {Object} snakeHead - 蛇头位置 {x, y}
     * @returns {boolean} 是否发生碰撞
     */
    checkCollision(snakeHead) {
        return (
            snakeHead.x === this.food.position.x &&
            snakeHead.y === this.food.position.y
        );
    }

    /**
     * 获取当前食物位置
     * @returns {Object} 食物位置 {x, y}
     */
    getFoodPosition() {
        return { ...this.food.position };
    }

    /**
     * 重置食物状态
     * @param {Array} snakeBody - 蛇的身体坐标数组
     */
    reset(snakeBody = []) {
        this.generateFood(snakeBody);
    }
}

export default FoodManager;