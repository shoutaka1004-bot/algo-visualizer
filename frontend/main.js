// タブ切り替え（迷路／ソート）
document.addEventListener('DOMContentLoaded', () => {
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabPanels = document.querySelectorAll('.tab-panel');

  function activateTab(tabName) {
    tabButtons.forEach((button) => {
      button.classList.toggle('is-active', button.dataset.tab === tabName);
    });
    tabPanels.forEach((panel) => {
      panel.hidden = panel.id !== `${tabName}-panel`;
    });
  }

  tabButtons.forEach((button) => {
    button.addEventListener('click', () => {
      activateTab(button.dataset.tab);
    });
  });

  const initialButton = document.querySelector('.tab-button.is-active') || tabButtons[0];
  if (initialButton) {
    activateTab(initialButton.dataset.tab);
  }
});

// 迷路生成（「迷路を生成する」ボタン押下 → /api/maze 呼び出し → Canvas描画）
document.addEventListener('DOMContentLoaded', () => {
  const generateMazeBtn = document.getElementById('generate-maze-btn');
  const mazeWidthInput = document.getElementById('maze-width');
  const mazeHeightInput = document.getElementById('maze-height');
  const mazeCanvas = document.getElementById('maze-canvas');

  if (!generateMazeBtn || !mazeWidthInput || !mazeHeightInput || !mazeCanvas) {
    return;
  }

  const MAX_CANVAS_SIZE = 600;
  const MIN_CELL_SIZE = 4;
  const MAX_CELL_SIZE = 24;

  function drawMaze(mazeData) {
    const cellSize = Math.min(
      MAX_CELL_SIZE,
      Math.max(
        MIN_CELL_SIZE,
        Math.floor(MAX_CANVAS_SIZE / Math.max(mazeData.width, mazeData.height))
      )
    );

    mazeCanvas.width = cellSize * mazeData.width;
    mazeCanvas.height = cellSize * mazeData.height;

    const ctx = mazeCanvas.getContext('2d');
    const rootStyle = getComputedStyle(document.documentElement);
    const wallColor = rootStyle.getPropertyValue('--color-main').trim();
    const pathColor = rootStyle.getPropertyValue('--color-base-bg').trim();

    for (let y = 0; y < mazeData.height; y += 1) {
      for (let x = 0; x < mazeData.width; x += 1) {
        ctx.fillStyle = mazeData.grid[y][x] ? wallColor : pathColor;
        ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
      }
    }
  }

  generateMazeBtn.addEventListener('click', async () => {
    const width = Number(mazeWidthInput.value);
    const height = Number(mazeHeightInput.value);

    const originalLabel = generateMazeBtn.textContent;
    generateMazeBtn.disabled = true;
    generateMazeBtn.textContent = '生成中…';

    try {
      const response = await fetch('/api/maze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ width, height }),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        console.error('迷路の生成に失敗しました:', errorBody.error || response.status);
        return;
      }

      const mazeData = await response.json();
      drawMaze(mazeData);
    } catch (err) {
      console.error('迷路の生成中にエラーが発生しました:', err);
    } finally {
      generateMazeBtn.disabled = false;
      generateMazeBtn.textContent = originalLabel;
    }
  });
});
