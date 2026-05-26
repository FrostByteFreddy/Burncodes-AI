import { onMounted, onUnmounted } from 'vue';

/**
 * Keeps --app-height in sync with the visible viewport (visualViewport.height).
 *
 * WHY NOT mess with document.body.height:
 *   When iOS Safari scrolls the page to bring a focused input into view, the
 *   body scroll offset increases. If we simultaneously shrink body.height to
 *   visualViewport.height the chat container (at body top = 0) scrolls
 *   completely out of the visible area → black screen.
 *
 * CORRECT APPROACH:
 *   Use `position: fixed` on the chat-page container (Chat.vue / ShareView.vue)
 *   so it's anchored to the viewport and immune to page scroll. Then only
 *   update --app-height so the container shrinks to the available space above
 *   the keyboard. Flexbox inside (header / scrollable main / sticky footer)
 *   redistributes naturally within the smaller fixed container.
 */
export function useAppHeight() {
  const update = () => {
    const h = window.visualViewport?.height ?? window.innerHeight;
    document.documentElement.style.setProperty('--app-height', `${h}px`);
  };

  onMounted(() => {
    update();
    window.addEventListener('resize', update);
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', update);
    }
  });

  onUnmounted(() => {
    window.removeEventListener('resize', update);
    if (window.visualViewport) {
      window.visualViewport.removeEventListener('resize', update);
    }
  });
}
