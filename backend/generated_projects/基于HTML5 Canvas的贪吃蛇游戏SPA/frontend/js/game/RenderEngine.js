class RenderEngine {
    constructor(canvasId, config) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.config = config;
        
        // 颜色配置
        this.colors = {
            background: '#1a1a2e',
            grid: '#16213e',
            snakeHead: '#4ecca3',
            snakeBody: '#4ecca3',
            food: '#ff6b6b',
            text: '#eeeeee',
            overlay: 'rgba(0, 0, 0, 0.7)'
        };
        
        // 字体配置
        this.fonts = {
            score: '24px Arial',
            title: '48px Arial',
            subtitle: '24px Arial',
            instruction: '18px Arial'
        };
        
        // 初始化Canvas尺寸
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }
    
    /**
     * 调整Canvas尺寸以适应容器
     */
    resizeCanvas() {
        const container = this.canvas.parentElement;
        if (container) {
            this.canvas.width = container.clientWidth;
            this.canvas.height = container.clientHeight;
        }
    }
    
    /**
     * 清除整个Canvas
     */
    clearCanvas() {
        this.ctx.fillStyle = this.colors.background;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    /**
     * 绘制网格背景
     */
    drawGrid() {
        const gridSize = this.config.gridSize;
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        this.ctx.strokeStyle = this.colors.grid;
        this.ctx.lineWidth = 1;
        
        // 绘制垂直线
        for (let x = 0; x <= width; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, height);
            this.ctx.stroke();
        }
        
        // 绘制水平线
        for (let y = 0; y <= height; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(width, y);
            this.ctx.stroke();
        }
    }
    
    /**
     * 绘制蛇
     * @param {Array} snakeBody - 蛇身体的坐标数组
     */
    drawSnake(snakeBody) {
        if (!snakeBody || snakeBody.length === 0) return;
        
        const gridSize = this.config.gridSize;
        
        // 绘制蛇身体
        for (let i = 0; i < snakeBody.length; i++) {
            const segment = snakeBody[i];
            const x = segment.x * gridSize;
            const y = segment.y * gridSize;
            
            // 蛇头使用不同颜色
            if (i === 0) {
                this.ctx.fillStyle = this.colors.snakeHead;
            } else {
                this.ctx.fillStyle = this.colors.snakeBody;
                // 身体部分稍微透明
                this.ctx.globalAlpha = 0.8;
            }
            
            // 绘制圆角矩形
            this.drawRoundedRect(x, y, gridSize, gridSize, 4);
            
            // 重置透明度
            this.ctx.globalAlpha = 1.0;
            
            // 绘制蛇眼睛（只在头部）
            if (i === 0) {
                this.drawSnakeEyes(x, y, gridSize);
            }
        }
    }
    
    /**
     * 绘制圆角矩形
     */
    drawRoundedRect(x, y, width, height, radius) {
        this.ctx.beginPath();
        this.ctx.moveTo(x + radius, y);
        this.ctx.lineTo(x + width - radius, y);
        this.ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        this.ctx.lineTo(x + width, y + height - radius);
        this.ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        this.ctx.lineTo(x + radius, y + height);
        this.ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        this.ctx.lineTo(x, y + radius);
        this.ctx.quadraticCurveTo(x, y, x + radius, y);
        this.ctx.closePath();
        this.ctx.fill();
    }
    
    /**
     * 绘制蛇眼睛
     */
    drawSnakeEyes(headX, headY, gridSize) {
        const eyeSize = gridSize / 5;
        const eyeOffset = gridSize / 3;
        
        this.ctx.fillStyle = '#000000';
        
        // 左眼
        this.ctx.beginPath();
        this.ctx.arc(headX + eyeOffset, headY + eyeOffset, eyeSize, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 右眼
        this.ctx.beginPath();
        this.ctx.arc(headX + gridSize - eyeOffset, headY + eyeOffset, eyeSize, 0, Math.PI * 2);
        this.ctx.fill();
    }
    
    /**
     * 绘制食物
     * @param {Object} foodPosition - 食物的坐标
     */
    drawFood(foodPosition) {
        if (!foodPosition) return;
        
        const gridSize = this.config.gridSize;
        const x = foodPosition.x * gridSize;
        const y = foodPosition.y * gridSize;
        
        // 绘制食物（苹果形状）
        this.ctx.fillStyle = this.colors.food;
        
        // 绘制主体（圆形）
        this.ctx.beginPath();
        this.ctx.arc(x + gridSize/2, y + gridSize/2, gridSize/2 - 2, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 绘制茎
        this.ctx.fillStyle = '#2e7d32';
        this.ctx.fillRect(x + gridSize/2 - 1, y, 2, gridSize/4);
        
        // 绘制叶子
        this.ctx.beginPath();
        this.ctx.moveTo(x + gridSize/2, y + gridSize/4);
        this.ctx.lineTo(x + gridSize/2 + gridSize/4, y);
        this.ctx.lineTo(x + gridSize/2, y + gridSize/8);
        this.ctx.closePath();
        this.ctx.fill();
    }
    
    /**
     * 绘制分数
     * @param {number} score - 当前分数
     */
    drawScore(score) {
        this.ctx.fillStyle = this.colors.text;
        this.ctx.font = this.fonts.score;
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'top';
        
        const scoreText = `得分: ${score}`;
        this.ctx.fillText(scoreText, 20, 20);
    }
    
    /**
     * 绘制游戏开始界面
     */
    drawStartScreen() {
        this.clearCanvas();
        this.drawGrid();
        
        // 半透明覆盖层
        this.ctx.fillStyle = this.colors.overlay;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 游戏标题
        this.ctx.fillStyle = this.colors.text;
        this.ctx.font = this.fonts.title;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        const title = '贪吃蛇大冒险';
        this.ctx.fillText(title, this.canvas.width / 2, this.canvas.height / 2 - 60);
        
        // 开始提示
        this.ctx.font = this.fonts.subtitle;
        const startText = '按空格键或点击开始按钮开始游戏';
        this.ctx.fillText(startText, this.canvas.width / 2, this.canvas.height / 2);
        
        // 操作说明
        this.ctx.font = this.fonts.instruction;
        const controlsText = '使用方向键 ↑ ↓ ← → 控制蛇的移动';
        this.ctx.fillText(controlsText, this.canvas.width / 2, this.canvas.height / 2 + 40);
        
        // 作者信息
        const authorText = 'HTML5 Canvas 游戏';
        this.ctx.fillText(authorText, this.canvas.width / 2, this.canvas.height - 40);
    }
    
    /**
     * 绘制游戏暂停界面
     */
    drawPauseScreen() {
        // 半透明覆盖层
        this.ctx.fillStyle = this.colors.overlay;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 暂停文字
        this.ctx.fillStyle = this.colors.text;
        this.ctx.font = this.fonts.title;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        const pauseText = '游戏暂停';
        this.ctx.fillText(pauseText, this.canvas.width / 2, this.canvas.height / 2 - 30);
        
        // 继续提示
        this.ctx.font = this.fonts.subtitle;
        const continueText = '按空格键继续游戏';
        this.ctx.fillText(continueText, this.canvas.width / 2, this.canvas.height / 2 + 30);
    }
    
    /**
     * 绘制游戏结束界面
     * @param {number} finalScore - 最终得分
     */
    drawGameOverScreen(finalScore) {
        // 半透明覆盖层
        this.ctx.fillStyle = this.colors.overlay;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 游戏结束文字
        this.ctx.fillStyle = this.colors.text;
        this.ctx.font = this.fonts.title;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        const gameOverText = '游戏结束';
        this.ctx.fillText(gameOverText, this.canvas.width / 2, this.canvas.height / 2 - 60);
        
        // 最终得分
        this.ctx.font = this.fonts.subtitle;
        const scoreText = `最终得分: ${finalScore}`;
        this.ctx.fillText(scoreText, this.canvas.width / 2, this.canvas.height / 2);
        
        // 重新开始提示
        const restartText = '按空格键重新开始游戏';
        this.ctx.fillText(restartText, this.canvas.width / 2, this.canvas.height / 2 + 60);
    }
    
    /**
     * 渲染完整游戏画面
     * @param {Object} gameState - 游戏状态
     * @param {Array} snakeBody - 蛇身体坐标
     * @param {Object} foodPosition - 食物坐标
     * @param {number} score - 当前分数
     */
    render(gameState, snakeBody, foodPosition, score) {
        this.clearCanvas();
        
        // 根据游戏状态渲染不同界面
        if (gameState.isGameOver) {
            this.drawGrid();
            this.drawSnake(snakeBody);
            this.drawFood(foodPosition);
            this.drawScore(score);
            this.drawGameOverScreen(score);
        } else if (!gameState.isRunning) {
            this.drawStartScreen();
        } else if (gameState.isPaused) {
            this.drawGrid();
            this.drawSnake(snakeBody);
            this.drawFood(foodPosition);
            this.drawScore(score);
            this.drawPauseScreen();
        } else {
            // 正常游戏画面
            this.drawGrid();
            this.drawSnake(snakeBody);
            this.drawFood(foodPosition);
            this.drawScore(score);
        }
    }
    
    /**
     * 绘制调试信息（可选）
     * @param {Object} debugInfo - 调试信息对象
     */
    drawDebugInfo(debugInfo) {
        if (!debugInfo) return;
        
        this.ctx.fillStyle = '#ffff00';
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'top';
        
        let y = 50;
        const lineHeight = 18;
        
        for (const [key, value] of Object.entries(debugInfo)) {
            this.ctx.fillText(`${key}: ${value}`, 20, y);
            y += lineHeight;
        }
    }
}

export default RenderEngine;