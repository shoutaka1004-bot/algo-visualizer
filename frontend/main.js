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
  const mazeErrorEl = document.getElementById('maze-error');
  const algorithmDescriptionEl = document.getElementById('algorithm-description');

  if (
    !generateMazeBtn ||
    !mazeWidthInput ||
    !mazeHeightInput ||
    !mazeCanvas ||
    !algorithmSelect ||
    !solveMazeBtn ||
    !mazeErrorEl
  ) {
    return;
  }

  // 選択中の探索アルゴリズムに応じた短い説明文（タスク32、フィードバック対応）。
  // #algorithm-descriptionが無くても迷路の生成・探索という主要機能は
  // 止めたくないため、algorithmDescriptionElの有無で個別にガードする。
  const algorithmDescriptions = {
    bfs: 'スタート地点から近い順に、一歩ずつ全方向を均等に調べていく方法です。全ての移動が同じコストのときに、必ず最短経路を見つけられます。',
    dijkstra: 'スタート地点から「ここまでの合計コストが一番小さいマス」を優先して調べていく方法です。今回の迷路は全マスの移動コストが同じなのでBFSと同じ結果になりますが、コストが異なる道にも対応できる汎用的な方法です。',
    astar: 'ゴールまでの距離の見積もり（ヒューリスティック）を使い、ゴールに近づきそうな方向を優先して調べる方法です。BFSやダイクストラ法より無駄な探索が少なく、同じ最短経路をより効率的に見つけられます。',
  };

  if (algorithmDescriptionEl) {
    algorithmSelect.addEventListener('change', () => {
      algorithmDescriptionEl.textContent = algorithmDescriptions[algorithmSelect.value] || '';
    });
  }

  // 技術的な詳細（例外名・HTTPステータスコード）を画面に出さず、次にとるべき
  // 行動が分かる平易な文言だけを表示する（BRIEF.md 4-6節の教訓に準拠）。
  // 「⚠」アイコンは色以外の区別手段として付与する。
  function showError(el, message) {
    el.textContent = `⚠ ${message}`;
    el.hidden = false;
  }

  function hideError(el) {
    el.hidden = true;
    el.textContent = '';
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

  // #speed-selectの値からアニメーション時間の倍率を取得する。
  // slow=3, normal=1.5, fast=1。要素が見つからない場合や想定外の値の場合は
  // 既定値の'normal'(1.5)として扱う。
  function getSpeedMultiplier() {
    const speedSelect = document.getElementById('speed-select');
    const value = speedSelect ? speedSelect.value : 'normal';
    if (value === 'slow') return 3;
    if (value === 'fast') return 1;
    return 1.5;
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
    // 上限・目標合計時間・pathの固定間隔には#speed-selectの倍率を掛けて
    // 速度選択を反映する。下限はちらつき・CPU負荷を避けるための別目的の
    // 値なので倍率を掛けず据え置く。
    const speedMultiplier = getSpeedMultiplier();
    const TOTAL_VISIT_DURATION_MS = 2500 * speedMultiplier;
    const MIN_VISIT_INTERVAL_MS = 4;
    const MAX_VISIT_INTERVAL_MS = 30 * speedMultiplier;
    const visitInterval = Math.min(
      MAX_VISIT_INTERVAL_MS,
      Math.max(MIN_VISIT_INTERVAL_MS, TOTAL_VISIT_DURATION_MS / Math.max(visitSteps.length, 1))
    );
    const PATH_CELL_INTERVAL_MS = 20 * speedMultiplier;

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

    hideError(mazeErrorEl);
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
        showError(
          mazeErrorEl,
          errorBody.error || '迷路の生成に失敗しました。入力値を確認して再度お試しください。'
        );
        return;
      }

      const mazeData = await response.json();
      currentMazeData = mazeData;
      drawMaze(mazeData);
    } catch (err) {
      console.error('迷路の生成中にエラーが発生しました:', err);
      showError(mazeErrorEl, '通信に失敗しました。ネットワーク接続を確認し、再度お試しください。');
    } finally {
      generateMazeBtn.disabled = false;
      generateMazeBtn.textContent = originalLabel;
      solveMazeBtn.disabled = false;
    }
  });

  solveMazeBtn.addEventListener('click', async () => {
    hideError(mazeErrorEl);

    if (!currentMazeData) {
      console.error('迷路がまだ生成されていません。先に「迷路を生成する」を押してください。');
      showError(mazeErrorEl, '迷路がまだ生成されていません。先に「迷路を生成する」を押してください。');
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
        showError(
          mazeErrorEl,
          errorBody.error || '探索に失敗しました。迷路を生成し直して再度お試しください。'
        );
        return;
      }

      const { steps } = await response.json();
      await animateSolveSteps(steps);
    } catch (err) {
      console.error('探索中にエラーが発生しました:', err);
      showError(mazeErrorEl, '通信に失敗しました。ネットワーク接続を確認し、再度お試しください。');
    } finally {
      solveMazeBtn.disabled = false;
      solveMazeBtn.textContent = originalLabel;
      generateMazeBtn.disabled = false;
    }
  });
});

// ソート実行（「ソートを開始する」→ /api/sort → バーチャートアニメーション）
document.addEventListener('DOMContentLoaded', () => {
  const sortSizeInput = document.getElementById('sort-size');
  const sortAlgorithmSelect = document.getElementById('sort-algorithm-select');
  const startSortBtn = document.getElementById('start-sort-btn');
  const sortCanvas = document.getElementById('sort-canvas');
  const sortErrorEl = document.getElementById('sort-error');
  const sortAlgorithmDescriptionEl = document.getElementById('sort-algorithm-description');

  if (!sortSizeInput || !sortAlgorithmSelect || !startSortBtn || !sortCanvas || !sortErrorEl) {
    return;
  }

  // 選択中の並び替えアルゴリズムに応じた短い説明文（タスク33、迷路タブと同じパターン）。
  // #sort-algorithm-descriptionが無くてもソートという主要機能は止めたくないため、
  // sortAlgorithmDescriptionElの有無で個別にガードする。
  const sortAlgorithmDescriptions = {
    bubble: '隣り合う2つの値を比較し、順番が逆なら入れ替える、という操作を配列の端から端まで繰り返す方法です。仕組みが単純な分、要素数が多いと時間がかかります。',
    quick: '基準となる値（ピボット）を1つ選び、それより小さい値・大きい値に配列を分割することを繰り返す方法です。多くの場合バブルソートより高速です。',
    merge: '配列を半分に分割することを繰り返して十分小さくしたあと、整列済みの小さな配列同士を合体（マージ）させながら1つに戻していく方法です。データの並び方に関わらず安定した速さで処理できます。',
  };

  if (sortAlgorithmDescriptionEl) {
    sortAlgorithmSelect.addEventListener('change', () => {
      sortAlgorithmDescriptionEl.textContent = sortAlgorithmDescriptions[sortAlgorithmSelect.value] || '';
    });
  }

  // 迷路タブと同じ表示・非表示ロジック（BRIEF.md 4-6節の教訓に準拠）。
  // DOMContentLoadedブロックが分かれているため、ここでも同一の定義を持つ。
  function showError(el, message) {
    el.textContent = `⚠ ${message}`;
    el.hidden = false;
  }

  function hideError(el) {
    el.hidden = true;
    el.textContent = '';
  }

  const SORT_CANVAS_WIDTH = 760;
  const SORT_CANVAS_HEIGHT = 320;
  const BAR_GAP_RATIO = 0.1;
  const VALUE_MIN = 1;
  const VALUE_MAX = 100;

  // ソート中に描画が参照する「現在表示中の配列」。APIは最終的なソート済み
  // 配列そのものは返さず、compare/swap/overwriteのステップ列だけを返すため、
  // ここでステップを1件ずつ適用しながら状態を再現する。
  let currentValues = [];

  function generateRandomValues(size) {
    const values = [];
    for (let i = 0; i < size; i += 1) {
      values.push(Math.floor(Math.random() * (VALUE_MAX - VALUE_MIN + 1)) + VALUE_MIN);
    }
    return values;
  }

  // 16進カラーコードを指定の不透明度のrgba()文字列に変換する（迷路タブの
  // hexToRgbaと同じ変換ロジック。配色を3系統に留めるため、ここでも
  // --color-accentのアルファ値違いだけで状態を描き分ける）。
  function hexToRgba(hex, alpha) {
    const normalized = hex.replace('#', '');
    const r = parseInt(normalized.substring(0, 2), 16);
    const g = parseInt(normalized.substring(2, 4), 16);
    const b = parseInt(normalized.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  // #speed-selectの値からアニメーション時間の倍率を取得する（迷路タブの
  // getSpeedMultiplierと同じ実装。DOMContentLoadedブロックが分かれている
  // ため、ここでも同一の定義を持つ）。
  function getSpeedMultiplier() {
    const speedSelect = document.getElementById('speed-select');
    const value = speedSelect ? speedSelect.value : 'normal';
    if (value === 'slow') return 3;
    if (value === 'fast') return 1;
    return 1.5;
  }

  // currentValuesの内容をバーチャートとして描画する。
  // highlightIndices（Set）に含まれるインデックスのバーはhighlightColorで、
  // それ以外は通常色（--color-main）で塗る。
  function drawBars(values, maxValue, highlightIndices, highlightColor) {
    sortCanvas.width = SORT_CANVAS_WIDTH;
    sortCanvas.height = SORT_CANVAS_HEIGHT;

    const ctx = sortCanvas.getContext('2d');
    const rootStyle = getComputedStyle(document.documentElement);
    const normalColor = rootStyle.getPropertyValue('--color-main').trim();

    ctx.clearRect(0, 0, sortCanvas.width, sortCanvas.height);

    const n = values.length;
    if (n === 0) {
      return;
    }
    const slotWidth = sortCanvas.width / n;
    const barWidth = Math.max(1, slotWidth * (1 - BAR_GAP_RATIO));

    for (let i = 0; i < n; i += 1) {
      const barHeight = (values[i] / maxValue) * sortCanvas.height;
      const isHighlighted = highlightIndices && highlightIndices.has(i);
      ctx.fillStyle = isHighlighted ? highlightColor : normalColor;
      ctx.fillRect(
        i * slotWidth,
        sortCanvas.height - barHeight,
        barWidth,
        barHeight
      );
    }
  }

  // ステップ列（compare/swap/overwrite）を、目標総時間内に収まるよう
  // バッチ処理しながら順に適用し、Canvasを再描画するアニメーション。
  //
  // バブルソートは配列サイズ上限200・最悪ケース（降順に近い配列）だと
  // 数万ステップに達しうる。1ステップ=1回の再描画（迷路タブの
  // animateSolveStepsと同じ方式）をそのまま使うと、1ステップあたり
  // 数msにクランプしても総時間が数分になりかねない。そのため、総時間の
  // 上限（MAX_TOTAL_DURATION_MS）を固定し、ステップ数が多い場合は
  // 複数ステップを1回の描画更新にまとめて適用することで、再描画の回数
  // 自体を一定数（maxTicks）以内に抑える。
  function animateSortSteps(steps, initialValues, maxValue) {
    // 目標合計時間・tickIntervalの上限には#speed-selectの倍率を掛けて
    // 速度選択を反映する。下限はちらつき・CPU負荷を避けるための別目的の
    // 値なので倍率を掛けず据え置く。
    const speedMultiplier = getSpeedMultiplier();
    const MAX_TOTAL_DURATION_MS = 6000 * speedMultiplier;
    const MIN_TICK_INTERVAL_MS = 15;
    const MAX_TICK_INTERVAL_MS = 60 * speedMultiplier;

    const totalSteps = steps.length;
    if (totalSteps === 0) {
      drawBars(initialValues, maxValue, null, null);
      return Promise.resolve();
    }

    const maxTicks = Math.floor(MAX_TOTAL_DURATION_MS / MIN_TICK_INTERVAL_MS);
    const stepsPerTick = Math.max(1, Math.ceil(totalSteps / maxTicks));
    const tickCount = Math.ceil(totalSteps / stepsPerTick);
    const tickInterval = Math.min(
      MAX_TICK_INTERVAL_MS,
      Math.max(MIN_TICK_INTERVAL_MS, MAX_TOTAL_DURATION_MS / tickCount)
    );

    const rootStyle = getComputedStyle(document.documentElement);
    const accentHex = rootStyle.getPropertyValue('--color-accent').trim();
    const compareColor = hexToRgba(accentHex, 0.45);
    const changedColor = hexToRgba(accentHex, 1);

    return new Promise((resolve) => {
      function applyStep(step) {
        if (step.type === 'compare') {
          return { indices: new Set(step.indices), color: compareColor };
        }
        if (step.type === 'swap') {
          const [a, b] = step.indices;
          const tmp = currentValues[a];
          currentValues[a] = currentValues[b];
          currentValues[b] = tmp;
          return { indices: new Set(step.indices), color: changedColor };
        }
        if (step.type === 'overwrite') {
          currentValues[step.index] = step.value;
          return { indices: new Set([step.index]), color: changedColor };
        }
        return { indices: new Set(), color: null };
      }

      function runTick(stepIndex) {
        if (stepIndex >= totalSteps) {
          // 完了後は、ハイライト無しの通常状態で最終描画する。
          drawBars(currentValues, maxValue, null, null);
          resolve();
          return;
        }

        const end = Math.min(stepIndex + stepsPerTick, totalSteps);
        let lastResult = { indices: new Set(), color: null };
        for (let i = stepIndex; i < end; i += 1) {
          lastResult = applyStep(steps[i]);
        }

        drawBars(currentValues, maxValue, lastResult.indices, lastResult.color);
        setTimeout(() => runTick(end), tickInterval);
      }

      runTick(0);
    });
  }

  startSortBtn.addEventListener('click', async () => {
    const size = Number(sortSizeInput.value);
    const algorithm = sortAlgorithmSelect.value;

    hideError(sortErrorEl);
    const originalLabel = startSortBtn.textContent;
    startSortBtn.disabled = true;
    startSortBtn.textContent = 'ソート中…';

    try {
      currentValues = generateRandomValues(size);
      const maxValue = Math.max(...currentValues, 1);
      drawBars(currentValues, maxValue, null, null);

      const response = await fetch('/api/sort', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ values: currentValues, algorithm }),
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        console.error('ソートに失敗しました:', errorBody.error || response.status);
        showError(
          sortErrorEl,
          errorBody.error || 'ソートに失敗しました。入力値を確認して再度お試しください。'
        );
        return;
      }

      const { steps } = await response.json();
      await animateSortSteps(steps, currentValues, maxValue);
    } catch (err) {
      console.error('ソート中にエラーが発生しました:', err);
      showError(sortErrorEl, '通信に失敗しました。ネットワーク接続を確認し、再度お試しください。');
    } finally {
      startSortBtn.disabled = false;
      startSortBtn.textContent = originalLabel;
    }
  });
});
