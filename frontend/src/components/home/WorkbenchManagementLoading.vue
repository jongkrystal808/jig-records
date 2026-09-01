<template>
  <section class="workbench-management-loading" aria-busy="true" aria-label="正在載入工作台管理後臺">
    <header><span class="brand-block">FM</span><div><small>Fixture-M Lite</small><strong>工作台管理後臺</strong></div></header>
    <div class="loading-columns">
      <aside><span></span><span></span><span></span></aside>
      <main><div class="loading-title"></div><div class="loading-card"></div><div class="loading-table"></div></main>
      <aside><div class="loading-title"></div><div class="loading-card"></div></aside>
    </div>
  </section>
</template>

<style scoped>
.workbench-management-loading { min-height: 100dvh; padding: 10px; color: #18263a; background: radial-gradient(circle at 18% 0%, #f8fbff 0%, #edf3fb 34%, #e9eef5 100%); }
header { display: flex; align-items: center; gap: 10px; min-height: 78px; margin-bottom: 12px; padding: 12px 16px; border: 1px solid #d7dfeb; border-radius: 20px; background: #fff; box-shadow: 0 10px 28px rgba(28, 47, 84, .08); }
header div { display: grid; gap: 2px; } header small { color: #718096; } header strong { font-size: 1.2rem; }
.brand-block { display: grid; place-items: center; width: 46px; height: 46px; border-radius: 14px; color: #fff; background: linear-gradient(145deg, #4b89ff, #2f6ee5); font-weight: 900; }
.loading-columns { display: grid; grid-template-columns: minmax(220px, 22fr) minmax(600px, 58fr) minmax(220px, 20fr); gap: 12px; min-height: calc(100dvh - 112px); }
aside, main { padding: 18px; border: 1px solid #d7dfeb; border-radius: 20px; background: rgba(255,255,255,.94); box-shadow: 0 12px 34px rgba(28,47,84,.08); }
aside span, .loading-title, .loading-card, .loading-table { display: block; border-radius: 12px; background: linear-gradient(90deg, #eef3f9 20%, #f8fbff 50%, #eef3f9 80%); background-size: 220% 100%; animation: shimmer 1.1s linear infinite; }
aside span { height: 48px; margin-bottom: 10px; } .loading-title { width: 38%; height: 24px; margin-bottom: 18px; } .loading-card { height: 170px; margin-bottom: 16px; } .loading-table { height: 360px; }
@keyframes shimmer { to { background-position: -220% 0; } }
@media (max-width: 1080px) { .loading-columns { grid-template-columns: minmax(230px, 30fr) minmax(500px, 70fr); } .loading-columns > aside:last-child { grid-column: 1 / -1; min-height: 180px; } }
@media (prefers-reduced-motion: reduce) { aside span, .loading-title, .loading-card, .loading-table { animation: none; } }
</style>
