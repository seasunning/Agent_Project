// 贪吃蛇游戏 - 主入口文件
// 负责初始化游戏、设置事件监听器、启动游戏循环以及协调各模块之间的交互

// 游戏配置常量
const GAME_CONFIG = {
    GRID_SIZE: 20,
    CANVAS_WIDTH: 600,
    CANVAS_HEIGHT: 400,
    FRAME_RATE: 10, // 每秒帧数
    INITIAL_SNAKE_LENGTH: 3,
    INITIAL_DIRECTION: 'RIGHT'
};

// 游戏状态
let gameState = {
    isRunning: false,
    isPaused: false,
    isGameOver: false,
    currentScore: 0
};

// 游戏对象
let snake = {
    body: [],
    direction: GAME_CONFIG.INITIAL_DIRECTION,
    nextDirection: GAME_CONFIG.INITIAL_DIRECTION
};

let food = {
    position: { x: 0, y: 0 }
};

// DOM元素引用
let canvas, ctx, scoreDisplay, startButton, pauseButton, gameOverDisplay;

// 游戏循环相关
let gameLoopId = null;
let lastRenderTime = 0;

// 初始化游戏
function initializeGame() {
    console.log('初始化贪吃蛇游戏...');
    
    // 获取DOM元素
    canvas = document.getElementById('gameCanvas');
    ctx = canvas.getContext('2d');
    scoreDisplay = document.getElementById('score');
    startButton = document.getElementById('startButton');
    pauseButton = document.getElementById('pauseButton');
    gameOverDisplay = document.getElementById('gameOver');
    
    // 设置Canvas尺寸
    canvas.width = GAME_CONFIG.CANVAS_WIDTH;
    canvas.height = GAME_CONFIG.CANVAS_HEIGHT;
    
    // 初始化蛇
    initializeSnake();
    
    // 初始化食物
    generateFood();
    
    // 初始化游戏状态
    resetGameState();
    
    // 设置事件监听器
    setupEventListeners();
    
    // 渲染初始画面
    renderFrame();
    
    console.log('游戏初始化完成');
}

// 初始化蛇
function initializeSnake() {
    snake.body = [];
    snake.direction = GAME_CONFIG.INITIAL_DIRECTION;
    snake.nextDirection = GAME_CONFIG.INITIAL_DIRECTION;
    
    // 创建初始蛇身
    const startX = Math.floor(GAME_CONFIG.CANVAS_WIDTH / (2 * GAME_CONFIG.GRID_SIZE)) * GAME_CONFIG.GRID_SIZE;
    const startY = Math.floor(GAME_CONFIG.CANVAS_HEIGHT / (2 * GAME_CONFIG.GRID_SIZE)) * GAME_CONFIG.GRID_SIZE;
    
    for (let i = 0; i < GAME_CONFIG.INITIAL_SNAKE_LENGTH; i++) {
        snake.body.push({
            x: startX - i * GAME_CONFIG.GRID_SIZE,
            y: startY
        });
    }
}

// 生成食物
function generateFood() {
    // 确保食物不会生成在蛇身上
    let validPosition = false;
    let newFoodPosition;
    
    while (!validPosition) {
        newFoodPosition = {
            x: Math.floor(Math.random() * (GAME_CONFIG.CANVAS_WIDTH / GAME_CONFIG.GRID_SIZE)) * GAME_CONFIG.GRID_SIZE,
            y: Math.floor(Math.random() * (GAME_CONFIG.CANVAS_HEIGHT / GAME_CONFIG.GRID_SIZE)) * GAME_CONFIG.GRID_SIZE
        };
        
        validPosition = true;
        
        // 检查是否与蛇身重叠
        for (const segment of snake.body) {
            if (segment.x === newFoodPosition.x && segment.y === newFoodPosition.y) {
                validPosition = false;
                break;
            }
        }
    }
    
    food.position = newFoodPosition;
}

// 重置游戏状态
function resetGameState() {
    gameState = {
        isRunning: false,
        isPaused: false,
        isGameOver: false,
        currentScore: 0
    };
    
    // 更新UI
    updateUI();
}

// 设置事件监听器
function setupEventListeners() {
    // 键盘输入监听
    document.addEventListener('keydown', handleKeyPress);
    
    // 开始按钮
    if (startButton) {
        startButton.addEventListener('click', () => {
            if (gameState.isGameOver) {
                resetGame();
            } else {
                toggleGame();
            }
        });
    }
    
    // 暂停按钮
    if (pauseButton) {
        pauseButton.addEventListener('click', togglePause);
    }
}

// 处理键盘输入
function handleKeyPress(event) {
    switch (event.key) {
        case 'ArrowUp':
            if (snake.direction !== 'DOWN') {
                snake.nextDirection = 'UP';
            }
            break;
        case 'ArrowDown':
            if (snake.direction !== 'UP') {
                snake.nextDirection = 'DOWN';
            }
            break;
        case 'ArrowLeft':
            if (snake.direction !== 'RIGHT') {
                snake.nextDirection = 'LEFT';
            }
            break;
        case 'ArrowRight':
            if (snake.direction !== 'LEFT') {
                snake.nextDirection = 'RIGHT';
            }
            break;
        case ' ':
            // 空格键切换游戏状态
            event.preventDefault();
            if (gameState.isGameOver) {
                resetGame();
            } else {
                toggleGame();
            }
            break;
        case 'p':
        case 'P':
            // P键暂停/继续
            togglePause();
            break;
    }
}

// 切换游戏运行状态
function toggleGame() {
    if (!gameState.isRunning && !gameState.isGameOver) {
        startGame();
    } else if (gameState.isRunning) {
        stopGame();
    }
}

// 开始游戏
function startGame() {
    if (gameState.isRunning) return;
    
    gameState.isRunning = true;
    gameState.isPaused = false;
    
    // 启动游戏循环
    startGameLoop();
    
    updateUI();
    console.log('游戏开始');
}

// 停止游戏
function stopGame() {
    gameState.isRunning = false;
    
    // 停止游戏循环
    if (gameLoopId) {
        cancelAnimationFrame(gameLoopId);
        gameLoopId = null;
    }
    
    updateUI();
    console.log('游戏停止');
}

// 切换暂停状态
function togglePause() {
    if (!gameState.isRunning || gameState.isGameOver) return;
    
    gameState.isPaused = !gameState.isPaused;
    
    if (gameState.isPaused) {
        if (gameLoopId) {
            cancelAnimationFrame(gameLoopId);
            gameLoopId = null;
        }
        console.log('游戏暂停');
    } else {
        startGameLoop();
        console.log('游戏继续');
    }
    
    updateUI();
}

// 启动游戏循环
function startGameLoop() {
    if (gameLoopId) {
        cancelAnimationFrame(gameLoopId);
    }
    
    lastRenderTime = 0;
    gameLoopId = requestAnimationFrame(gameLoop);
}

// 游戏主循环
function gameLoop(currentTime) {
    if (!gameState.isRunning || gameState.isPaused || gameState.isGameOver) {
        return;
    }
    
    // 控制帧率
    const deltaTime = currentTime - lastRenderTime;
    const frameInterval = 1000 / GAME_CONFIG.FRAME_RATE;
    
    if (deltaTime >= frameInterval) {
        // 更新游戏逻辑
        updateGame();
        
        // 渲染画面
        renderFrame();
        
        lastRenderTime = currentTime - (deltaTime % frameInterval);
    }
    
    // 继续下一帧
    gameLoopId = requestAnimationFrame(gameLoop);
}

// 更新游戏逻辑
function updateGame() {
    // 更新蛇的方向
    snake.direction = snake.nextDirection;
    
    // 移动蛇
    moveSnake();
    
    // 检测碰撞
    checkCollisions();
}

// 移动蛇
function moveSnake() {
    // 获取蛇头
    const head = { ...snake.body[0] };
    
    // 根据方向移动蛇头
    switch (snake.direction) {
        case 'UP':
            head.y -= GAME_CONFIG.GRID_SIZE;
            break;
        case 'DOWN':
            head.y += GAME_CONFIG.GRID_SIZE;
            break;
        case 'LEFT':
            head.x -= GAME_CONFIG.GRID_SIZE;
            break;
        case 'RIGHT':
            head.x += GAME_CONFIG.GRID_SIZE;
            break;
    }
    
    // 将新头部添加到蛇身前面
    snake.body.unshift(head);
    
    // 移除尾部（除非吃到食物）
    // 这个逻辑在checkCollisions中处理
}

// 检测碰撞
function checkCollisions() {
    const head = snake.body[0];
    
    // 检测边界碰撞
    if (
        head.x < 0 || 
        head.x >= GAME_CONFIG.CANVAS_WIDTH || 
        head.y < 0 || 
        head.y >= GAME_CONFIG.CANVAS_HEIGHT
    ) {
        gameOver();
        return;
    }
    
    // 检测自身碰撞
    for (let i = 1; i < snake.body.length; i++) {
        if (head.x === snake.body[i].x && head.y === snake.body[i].y) {
            gameOver();
            return;
        }
    }
    
    // 检测食物碰撞
    if (head.x === food.position.x && head.y === food.position.y) {
        // 吃到食物，增加分数
        gameState.currentScore += 10;
        
        // 生成新食物
        generateFood();
        
        // 更新分数显示
        updateScoreDisplay();
        
        // 蛇身增长（不移除尾部）
        console.log('吃到食物！分数：' + gameState.currentScore);
    } else {
        // 没吃到食物，移除尾部
        snake.body.pop();
    }
}

// 游戏结束
function gameOver() {
    gameState.isRunning = false;
    gameState.isGameOver = true;
    
    // 停止游戏循环
    if (gameLoopId) {
        cancelAnimationFrame(gameLoopId);
        gameLoopId = null;
    }
    
    updateUI();
    console.log('游戏结束！最终分数：' + gameState.currentScore);
}

// 重置游戏
function resetGame() {
    console.log('重置游戏...');
    
    // 停止当前游戏循环
    if (gameLoopId) {
        cancelAnimationFrame(gameLoopId);
        gameLoopId = null;
    }
    
    // 重新初始化游戏
    initializeSnake();
    generateFood();
    resetGameState();
    
    // 渲染初始画面
    renderFrame();
    
    console.log('游戏重置完成');
}

// 渲染帧
function renderFrame() {
    // 清空画布
    ctx.clearRect(0, 0, GAME_CONFIG.CANVAS_WIDTH, GAME_CONFIG.CANVAS_HEIGHT);
    
    // 绘制网格背景（可选）
    drawGrid();
    
    // 绘制蛇
    drawSnake();
    
    // 绘制食物
    drawFood();
    
    // 绘制分数
    drawScore();
    
    // 如果游戏结束，绘制结束画面
    if (gameState.isGameOver) {
        drawGameOver();
    }
}

// 绘制网格
function drawGrid() {
    ctx.strokeStyle = '#f0f0f0';
    ctx.lineWidth = 0.5;
    
    // 绘制垂直线
    for (let x = 0; x <= GAME_CONFIG.CANVAS_WIDTH; x += GAME_CONFIG.GRID_SIZE) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, GAME_CONFIG.CANVAS_HEIGHT);
        ctx.stroke();
    }
    
    // 绘制水平线
    for (let y = 0; y <= GAME_CONFIG.CANVAS_HEIGHT; y += GAME_CONFIG.GRID_SIZE) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(GAME_CONFIG.CANVAS_WIDTH, y);
        ctx.stroke();
    }
}

// 绘制蛇
function drawSnake() {
    // 绘制蛇身
    for (let i = 0; i < snake.body.length; i++) {
        const segment = snake.body[i];
        
        // 蛇头用不同颜色
        if (i === 0) {
            ctx.fillStyle = '#4CAF50'; // 蛇头颜色
        } else {
            ctx.fillStyle = '#8BC34A'; // 蛇身颜色
        }
        
        // 绘制蛇身段
        ctx.fillRect(
            segment.x, 
            segment.y, 
            GAME_CONFIG.GRID_SIZE, 
            GAME_CONFIG.GRID_SIZE
        );
        
        // 绘制边框
        ctx.strokeStyle = '#388E3C';
        ctx.lineWidth = 1;
        ctx.strokeRect(
            segment.x, 
            segment.y, 
            GAME_CONFIG.GRID_SIZE, 
            GAME_CONFIG.GRID_SIZE
        );
    }
}

// 绘制食物
function drawFood() {
    ctx.fillStyle = '#FF5722'; // 食物颜色
    
    // 绘制食物
    ctx.beginPath();
    ctx.arc(
        food.position.x + GAME_CONFIG.GRID_SIZE / 2,
        food.position.y + GAME_CONFIG.GRID_SIZE / 2,
        GAME_CONFIG.GRID_SIZE / 2 - 1,
        0,
        Math.PI * 2
    );
    ctx.fill();
    
    // 绘制食物内部亮点
    ctx.fillStyle = '#FF8A65';
    ctx.beginPath();
    ctx.arc(
        food.position.x + GAME_CONFIG.GRID_SIZE / 3,
        food.position.y + GAME_CONFIG.GRID_SIZE / 3,
        GAME_CONFIG.GRID_SIZE / 6,
        0,
        Math.PI * 2
    );
    ctx.fill();
}

// 绘制分数
function drawScore() {
    ctx.fillStyle = '#333';
    ctx.font = '16px Arial';
    ctx.textAlign = 'left';
    ctx.fillText('分数: ' + gameState.currentScore, 10, 20);
}

// 绘制游戏结束画面
function drawGameOver() {
    // 半透明黑色背景
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(0, 0, GAME_CONFIG.CANVAS_WIDTH, GAME_CONFIG.CANVAS_HEIGHT);
    
    // 游戏结束文字
    ctx.fillStyle = '#FFF';
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('游戏结束', GAME_CONFIG.CANVAS_WIDTH / 2, GAME_CONFIG.CANVAS_HEIGHT / 2 - 30);
    
    // 最终分数
    ctx.font = '24px Arial';
    ctx.fillText('最终分数: ' + gameState.currentScore, GAME_CONFIG.CANVAS_WIDTH / 2, GAME_CONFIG.CANVAS_HEIGHT / 2 + 10);
    
    // 重新开始提示
    ctx.font = '18px Arial';
    ctx.fillText('按空格键或点击开始按钮重新开始', GAME_CONFIG.CANVAS_WIDTH / 2, GAME_CONFIG.CANVAS_HEIGHT / 2 + 50);
}

// 更新UI显示
function updateUI() {
    // 更新分数显示
    updateScoreDisplay();
    
    // 更新按钮状态
    if (startButton) {
        if (gameState.isGameOver) {
            startButton.textContent = '重新开始';
            startButton.disabled = false;
        } else if (gameState.isRunning) {
            startButton.textContent = '停止';
            startButton.disabled = false;
        } else {
            startButton.textContent = '开始';
            startButton.disabled = false;
        }
    }
    
    // 更新暂停按钮状态
    if (pauseButton) {
        if (gameState.isRunning && !gameState.isGameOver) {
            pauseButton.disabled = false;
            pauseButton.textContent = gameState.isPaused ? '继续' : '暂停';
        } else {
            pauseButton.disabled = true;
            pauseButton.textContent = '暂停';
        }
    }
    
    // 更新游戏结束显示
    if (gameOverDisplay) {
        gameOverDisplay.style.display = gameState.isGameOver ? 'block' : 'none';
    }
}

// 更新分数显示
function updateScoreDisplay() {
    if (scoreDisplay) {
        scoreDisplay.textContent = gameState.currentScore;
    }
}

// 页面加载完成后初始化游戏
window.addEventListener('DOMContentLoaded', initializeGame);

// 导出游戏控制函数（用于调试）
window.gameControls = {
    initializeGame,
    startGame,
    stopGame,
    togglePause,
    resetGame,
    getGameState: () => ({ ...gameState }),
    getSnake: () => ({ ...snake }),
    getFood: () => ({ ...food })
};

console.log('main.js 加载完成');