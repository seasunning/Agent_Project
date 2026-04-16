class GameController {
    constructor(config) {
        // 游戏配置
        this.config = {
            gridSize: config.gridSize || 20,
            canvasWidth: config.canvasWidth || 800,
            canvasHeight: config.canvasHeight || 600,
            frameRate: config.frameRate || 10
        };
        
        // 游戏状态
        this.gameState = {
            isRunning: false,
            isPaused: false,
            isGameOver: false,
            currentScore: 0
        };
        
        // 游戏模块实例（将在初始化时创建）
        this.snakeManager = null;
        this.foodManager = null;
        this.renderEngine = null;
        this.inputHandler = null;
        this.scoreManager = null;
        this.collisionDetector = null;
        
        // 游戏循环相关
        this.gameLoopId = null;
        this.lastFrameTime = 0;
        
        // 绑定方法
        this.handleKeyPress = this.handleKeyPress.bind(this);
        this.gameLoop = this.gameLoop.bind(this);
    }
    
    /**
     * 初始化游戏
     * @param {Object} dependencies - 依赖的模块实例
     */
    initializeGame(dependencies) {
        // 注入依赖模块
        this.snakeManager = dependencies.snakeManager;
        this.foodManager = dependencies.foodManager;
        this.renderEngine = dependencies.renderEngine;
        this.inputHandler = dependencies.inputHandler;
        this.scoreManager = dependencies.scoreManager;
        this.collisionDetector = dependencies.collisionDetector;
        
        // 初始化游戏状态
        this.resetGame();
        
        // 设置输入处理器
        this.inputHandler.setOnDirectionChange(this.handleKeyPress);
        
        // 初始渲染
        this.renderEngine.render(this.snakeManager.getSnake(), 
                                this.foodManager.getFood(), 
                                this.gameState);
        
        console.log('Game initialized successfully');
    }
    
    /**
     * 启动游戏
     */
    startGame() {
        if (this.gameState.isGameOver) {
            this.resetGame();
        }
        
        this.gameState.isRunning = true;
        this.gameState.isPaused = false;
        this.gameState.isGameOver = false;
        
        // 启动游戏循环
        this.startGameLoop();
        
        console.log('Game started');
    }
    
    /**
     * 暂停/恢复游戏
     */
    togglePause() {
        if (!this.gameState.isRunning || this.gameState.isGameOver) {
            return;
        }
        
        this.gameState.isPaused = !this.gameState.isPaused;
        
        if (this.gameState.isPaused) {
            this.stopGameLoop();
            console.log('Game paused');
        } else {
            this.startGameLoop();
            console.log('Game resumed');
        }
        
        // 更新渲染
        this.renderEngine.render(this.snakeManager.getSnake(), 
                                this.foodManager.getFood(), 
                                this.gameState);
    }
    
    /**
     * 重置游戏
     */
    resetGame() {
        // 停止当前游戏循环
        this.stopGameLoop();
        
        // 重置游戏状态
        this.gameState = {
            isRunning: false,
            isPaused: false,
            isGameOver: false,
            currentScore: 0
        };
        
        // 重置各模块
        if (this.snakeManager) {
            this.snakeManager.reset();
        }
        if (this.foodManager) {
            this.foodManager.reset();
        }
        if (this.scoreManager) {
            this.scoreManager.reset();
        }
        
        console.log('Game reset');
    }
    
    /**
     * 处理键盘输入
     * @param {string} direction - 方向指令
     */
    handleKeyPress(direction) {
        // 如果游戏未运行，按任意键开始游戏
        if (!this.gameState.isRunning && !this.gameState.isGameOver) {
            this.startGame();
            return;
        }
        
        // 如果游戏结束，按空格键重新开始
        if (this.gameState.isGameOver && direction === ' ') {
            this.resetGame();
            this.startGame();
            return;
        }
        
        // 如果游戏暂停，按空格键恢复
        if (this.gameState.isPaused && direction === ' ') {
            this.togglePause();
            return;
        }
        
        // 如果游戏运行中，处理方向键
        if (this.gameState.isRunning && !this.gameState.isPaused) {
            this.snakeManager.changeDirection(direction);
        }
    }
    
    /**
     * 启动游戏主循环
     */
    startGameLoop() {
        if (this.gameLoopId) {
            this.stopGameLoop();
        }
        
        this.lastFrameTime = performance.now();
        this.gameLoopId = requestAnimationFrame(this.gameLoop);
    }
    
    /**
     * 停止游戏主循环
     */
    stopGameLoop() {
        if (this.gameLoopId) {
            cancelAnimationFrame(this.gameLoopId);
            this.gameLoopId = null;
        }
    }
    
    /**
     * 游戏主循环
     * @param {number} currentTime - 当前时间戳
     */
    gameLoop(currentTime) {
        // 计算帧间隔
        const deltaTime = currentTime - this.lastFrameTime;
        const frameInterval = 1000 / this.config.frameRate;
        
        // 如果未达到帧间隔时间，继续等待
        if (deltaTime < frameInterval) {
            this.gameLoopId = requestAnimationFrame(this.gameLoop);
            return;
        }
        
        this.lastFrameTime = currentTime - (deltaTime % frameInterval);
        
        // 更新游戏逻辑
        this.updateGame();
        
        // 渲染游戏画面
        this.renderEngine.render(this.snakeManager.getSnake(), 
                                this.foodManager.getFood(), 
                                this.gameState);
        
        // 继续下一帧
        this.gameLoopId = requestAnimationFrame(this.gameLoop);
    }
    
    /**
     * 更新游戏逻辑
     */
    updateGame() {
        if (!this.gameState.isRunning || this.gameState.isPaused || this.gameState.isGameOver) {
            return;
        }
        
        // 移动蛇
        this.snakeManager.move();
        
        // 获取蛇头位置
        const snakeHead = this.snakeManager.getHead();
        
        // 检测边界碰撞
        if (this.collisionDetector.checkBoundaryCollision(snakeHead, this.config)) {
            this.gameOver();
            return;
        }
        
        // 检测自身碰撞
        if (this.snakeManager.checkSelfCollision()) {
            this.gameOver();
            return;
        }
        
        // 检测食物碰撞
        const food = this.foodManager.getFood();
        if (this.collisionDetector.checkFoodCollision(snakeHead, food)) {
            // 增加分数
            this.scoreManager.increaseScore();
            this.gameState.currentScore = this.scoreManager.getScore();
            
            // 生成新食物
            this.foodManager.generateFood(this.snakeManager.getSnake().body, this.config);
            
            // 增长蛇身
            this.snakeManager.grow();
        }
    }
    
    /**
     * 游戏结束处理
     */
    gameOver() {
        this.gameState.isRunning = false;
        this.gameState.isGameOver = true;
        this.stopGameLoop();
        
        console.log(`Game Over! Final Score: ${this.gameState.currentScore}`);
    }
    
    /**
     * 获取当前游戏状态
     * @returns {Object} 游戏状态对象
     */
    getGameState() {
        return { ...this.gameState };
    }
    
    /**
     * 获取游戏配置
     * @returns {Object} 游戏配置对象
     */
    getConfig() {
        return { ...this.config };
    }
}

export default GameController;