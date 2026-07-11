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

// 迷路生成・探索（「迷路を生成する」→ /api/maze、「探索を開始する」→ /api/maze/solve）
document.addEventListener('DOMContentLoaded', () => {
  const generateMazeBtn = document.getElementById('generate-maze-btn');
  const mazeWidthInput = document.getElementById('maze-width');
  const mazeHeightInput = document.getElementById('maze-height');
  const mazeCanvas = document.getElementById('maze-canvas');
  const algorithmSelect = document.getElementById('algorithm-select');
  const solveMazeBtn = document.getElementById('solve-maze-btn');

  if (
    !generateMazeBtn ||
    !mazeWidthInput ||
    !mazeHeightInput ||
    !mazeCanvas ||
    !algorithmSelect ||
    !solveMazeBtn
  ) {
    return;
  }

  const MAX_CANVAS_SIZE = 600;
  const MIN_CELL_SIZE = 4;
  const MAX_CELL_SIZE = 24;

  // 生成済みの迷路データとセルサイズ。「迷路を生成する」ハンドラと
  // 「探索を開始する」ハンドラの両方から参照できるよう、このDOMContentLoaded
  // ブロックのスコープに保持する（タスク20の申し送り事項への対応）。
  let currentMazeData = null;
  let currentCellSize = null;

  function drawMaze(mazeData) {
    const cellSize = Math.min(
      MAX_CELL_SIZE,
      Math.max(
        MIN_CELL_SIZE,
        Math.floor(MAX_CANVAS_SIZE / Math.max(mazeData.width, mazeData.height))
      )
    );
    currentCellSize = cellSize;

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

  // 16進カラーコード（例: "#FF9F45"）を指定の不透明度のrgba()文字列に変換する。
  // 配色は既存の3系統（--color-base-bg/--color-main/--color-accent）から
  // 増やさないという方針のもと、--color-accentのアルファ値違いだけで
  // 「訪問済みセル」と「最終経路」を描き分けるために使う。
  function hexToRgba(hex, alpha) {
    const normalized = hex.replace('#', '');
    const r = parseInt(normalized.substring(0, 2), 16);
    const g = parseInt(normalized.substring(2, 4), 16);
    const b = parseInt(normalized.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  // 探索ステップ列（visit → 最後にpath）をCanvas上にアニメーション表示する。
  // 離散的な1マスずつの描画なので、requestAnimationFrameで毎フレームの経過時間を
  // 蓄積して間引くよりも、setTimeoutの再帰呼び出しでステップごとに任意の待機時間を
  // 指定する方が単純で意図が明確なため、この方式を採用する。
  function animateSolveSteps(steps) {
    const visitSteps = steps.filter((step) => step.type === 'visit');
    const pathStep = steps.find((step) => step.type === 'path');

    const ctx = mazeCanvas.getContext('2d');
    const rootStyle = getComputedStyle(document.documentElement);
    const accentHex = rootStyle.getPropertyValue('--color-accent').trim();
    const visitedColor = hexToRgba(accentHex, 0.35);
    const pathColor = hexToRgba(accentHex, 1);

    // 迷路が大きく数百ステップになりうるため、visit全体の目標合計時間から
    // 1ステップあたりの間隔を逆算する（大きい迷路ほど描画に時間がかかるのは
    // 自然な挙動として許容し、下限4ms・上限30msでクランプする）。
    const TOTAL_VISIT_DURATION_MS = 2500;
    const MIN_VISIT_INTERVAL_MS = 4;
    const MAX_VISIT_INTERVAL_MS = 30;
    const visitInterval = Math.min(
      MAX_VISIT_INTERVAL_MS,
      Math.max(MIN_VISIT_INTERVAL_MS, TOTAL_VISIT_DURATION_MS / Math.max(visitSteps.length, 1))
    );
    const PATH_CELL_INTERVAL_MS = 20;

    return new Promise((resolve) => {
      function drawNextVisit(index) {
        if (index >= visitSteps.length) {
          drawPath(0);
          return;
        }
        const step = visitSteps[index];
        ctx.fillStyle = visitedColor;
        ctx.fillRect(
          step.x * currentCellSize,
          step.y * currentCellSize,
          currentCellSize,
          currentCellSize
        );
        setTimeout(() => drawNextVisit(index + 1), visitInterval);
      }

      function drawPath(index) {
        if (!pathStep || !Array.isArray(pathStep.cells) || index >= pathStep.cells.length) {
          resolve();
          return;
        }
        const [x, y] = pathStep.cells[index];
        ctx.fillStyle = pathColor;
        ctx.fillRect(x * currentCellSize, y * currentCellSize, currentCellSize, currentCellSize);
        setTimeout(() => drawPath(index + 1), PATH_CELL_INTERVAL_MS);
      }

      drawNextVisit(0);
    });
  }

  generateMazeBtn.addEventListener('click', async () => {
    const width = Number(mazeWidthInput.value);
    const height = Number(mazeHeightInput.value);

    const originalLabel = generateMazeBtn.textContent;
    generateMazeBtn.disabled = true;
    generateMazeBtn.textContent = '生成中…';
    // 生成中に探索が始まると、更新途中のcurrentMazeData/currentCellSizeを
    // 参照してしまう可能性があるため、探索ボタンも合わせてdisabledにする。
    solveMazeBtn.disabled = true;

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
      currentMazeData = mazeData;
      drawMaze(mazeData);
    } catch (err) {
      console.error('迷路の生成中にエラーが発生しました:', err);
    } finally {
      generateMazeBtn.disabled = false;
      generateMazeBtn.textContent = originalLabel;
      solveMazeBtn.disabled = false;
    }
  });

  solveMazeBtn.addEventListener('click', async () => {
    if (!currentMazeData) {
      console.error('迷路がまだ生成されていません。先に「迷路を生成する」を押してください。');
      return;
    }

    const algorithm = algorithmSelect.value;
    const originalLabel = solveMazeBtn.textContent;
    solveMazeBtn.disabled = true;
    solveMazeBtn.textContent = '探索中…';
    // 探索アニメーション中に迷路が再生成されると、アニメーションが参照している
    // currentCellSize・Canvasサイズと食い違うため、生成ボタンも合わせてdisabledにする。
    generateMazeBtn.disabled = true;

    try {
      // 前回のハイライトが残らないよう、アニメーション開始前に一度
      // 壁・通路の初期状態に描き直す。
      drawMaze(currentMazeData);

      const response = await fetch('/api/maze/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grid: currentMazeData.grid, algorithm }),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        console.error('探索に失敗しました:', errorBody.error || response.status);
        return;
      }

      const { steps } = await response.json();
      await animateSolveSteps(steps);
    } catch (err) {
      console.error('探索中にエラーが発生しました:', err);
    } finally {
      solveMazeBtn.disabled = false;
      solveMazeBtn.textContent = originalLabel;
      generateMazeBtn.disabled = false;
    }
  });
});
