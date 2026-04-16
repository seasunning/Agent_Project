class SnakeManager {
    constructor(config) {
        this.gridSize = config.gridSize;
        this.canvasWidth = config.canvasWidth;
        this.canvasHeight = config.canvasHeight;
        
        // 初始化蛇
        this.reset();
    }
    
    /**
     * 重置蛇的状态
     */
    reset() {
        // 蛇的初始位置在画布中央
        const startX = Math.floor(this.canvasWidth / this.gridSize / 2) * this.gridSize;
        const startY = Math.floor(this.canvasHeight / this.gridSize / 2) * this.gridSize;
        
        this.body = [
            { x: startX, y: startY },
            { x: startX - this.gridSize, y: startY },
            { x: startX - this.gridSize * 2, y: startY }
        ];
        
        this.direction = 'RIGHT';
        this.nextDirection = 'RIGHT';
        this.growPending = false;
    }
    
    /**
     * 更新蛇的移动方向
     * @param {string} newDirection - 新的方向 ('UP', 'DOWN', 'LEFT', 'RIGHT')
     */
    changeDirection(newDirection) {
        // 防止直接反向移动（例如从右直接到左）
        const oppositeDirections = {
            'UP': 'DOWN',
            'DOWN': 'UP',
            'LEFT': 'RIGHT',
            'RIGHT': 'LEFT'
        };
        
        if (newDirection && oppositeDirections[this.direction] !== newDirection) {
            this.nextDirection = newDirection;
        }
    }
    
    /**
     * 移动蛇
     */
    move() {
        // 更新当前方向
        this.direction = this.nextDirection;
        
        // 创建新的蛇头
        const head = { ...this.body[0] };
        
        // 根据方向移动蛇头
        switch (this.direction) {
            case 'UP':
                head.y -= this.gridSize;
                break;
            case 'DOWN':
                head.y += this.gridSize;
                break;
            case 'LEFT':
                head.x -= this.gridSize;
                break;
            case 'RIGHT':
                head.x += this.gridSize;
                break;
        }
        
        // 将新蛇头添加到身体前端
        this.body.unshift(head);
        
        // 如果不需要增长，移除尾部
        if (!this.growPending) {
            this.body.pop();
        } else {
            this.growPending = false;
        }
    }
    
    /**
     * 标记蛇需要增长（当吃到食物时调用）
     */
    grow() {
        this.growPending = true;
    }
    
    /**
     * 检测蛇头是否与自身发生碰撞
     * @returns {boolean} - 如果发生碰撞返回true
     */
    checkSelfCollision() {
        const head = this.body[0];
        
        // 检查蛇头是否与身体的任何其他部分重叠
        for (let i = 1; i < this.body.length; i++) {
            if (head.x === this.body[i].x && head.y === this.body[i].y) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * 检测蛇头是否与边界发生碰撞
     * @returns {boolean} - 如果发生碰撞返回true
     */
    checkBoundaryCollision() {
        const head = this.body[0];
        
        return (
            head.x < 0 ||
            head.x >= this.canvasWidth ||
            head.y < 0 ||
            head.y >= this.canvasHeight
        );
    }
    
    /**
     * 检测蛇头是否与食物发生碰撞
     * @param {Object} foodPosition - 食物的位置 {x, y}
     * @returns {boolean} - 如果发生碰撞返回true
     */
    checkFoodCollision(foodPosition) {
        const head = this.body[0];
        return head.x === foodPosition.x && head.y === foodPosition.y;
    }
    
    /**
     * 获取蛇的当前位置数据
     * @returns {Object} - 包含蛇身体数组和方向的对象
     */
    getSnakeData() {
        return {
            body: this.body,
            direction: this.direction
        };
    }
    
    /**
     * 获取蛇头位置
     * @returns {Object} - 蛇头的位置 {x, y}
     */
    getHeadPosition() {
        return { ...this.body[0] };
    }
}

export default SnakeManager;