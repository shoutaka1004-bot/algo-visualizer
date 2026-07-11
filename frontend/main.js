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
