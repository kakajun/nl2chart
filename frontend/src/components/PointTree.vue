<template>
  <div class="point-tree">
    <div class="search-box">
      <input
        v-model="searchText"
        placeholder="搜索测点..."
        class="search-input"
      />
    </div>
    <div class="tree-content">
      <div
        v-for="cat in filteredCategories"
        :key="cat.id"
        class="category"
      >
        <div class="cat-header" @click="toggleCat(cat.id)">
          <span class="arrow" :class="{ expanded: expanded[cat.id] }">▶</span>
          <span class="cat-name">{{ cat.name }}</span>
          <span class="cat-count">{{ cat.points.length }}</span>
        </div>
        <div v-show="expanded[cat.id]" class="cat-points">
          <div
            v-for="pt in cat.points"
            :key="pt.code"
            class="point-item"
            :class="{ selected: selected.has(pt.code) }"
            @click="togglePoint(pt)"
          >
            <span class="pt-code">{{ pt.code }}</span>
            <span class="pt-name">{{ pt.name }}</span>
            <span class="pt-unit">{{ pt.unit }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="selection-bar">
      <span>已选 {{ selected.size }} 个</span>
      <button class="btn-clear" @click="clearAll">清空</button>
      <button class="btn-confirm" @click="confirm">查看趋势</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  categories: { type: Array, default: () => [] },
});

const emit = defineEmits(["select"]);

const searchText = ref("");
const expanded = ref({ env: true });
const selected = ref(new Set());

const filteredCategories = computed(() => {
  if (!searchText.value) return props.categories;
  const q = searchText.value.toLowerCase();
  return props.categories
    .map((cat) => ({
      ...cat,
      points: cat.points.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.code.toLowerCase().includes(q)
      ),
    }))
    .filter((cat) => cat.points.length > 0);
});

function toggleCat(id) {
  expanded.value[id] = !expanded.value[id];
}

function togglePoint(pt) {
  if (selected.value.has(pt.code)) {
    selected.value.delete(pt.code);
  } else {
    selected.value.add(pt.code);
  }
}

function clearAll() {
  selected.value.clear();
}

function confirm() {
  const codes = Array.from(selected.value);
  const points = [];
  for (const cat of props.categories) {
    for (const pt of cat.points) {
      if (selected.value.has(pt.code)) {
        points.push(pt);
      }
    }
  }
  emit("select", points);
}
</script>

<style scoped>
.point-tree {
  width: 280px;
  background: #111827;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.search-box {
  padding: 12px;
  border-bottom: 1px solid #1e293b;
}
.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #1e293b;
  border-radius: 6px;
  background: #0a0e1a;
  color: #e0e6ed;
  font-size: 13px;
  box-sizing: border-box;
}
.search-input:focus {
  outline: none;
  border-color: #4dabf7;
}
.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}
.category {
  margin-bottom: 4px;
}
.cat-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  font-size: 13px;
  color: #94a3b8;
}
.cat-header:hover {
  background: #1e293b;
}
.arrow {
  font-size: 10px;
  margin-right: 8px;
  transition: transform 0.2s;
  color: #64748b;
}
.arrow.expanded {
  transform: rotate(90deg);
}
.cat-name {
  flex: 1;
  font-weight: 500;
}
.cat-count {
  font-size: 11px;
  color: #64748b;
  background: #1e293b;
  padding: 2px 6px;
  border-radius: 4px;
}
.cat-points {
  padding-left: 12px;
}
.point-item {
  display: flex;
  align-items: center;
  padding: 6px 12px 6px 8px;
  cursor: pointer;
  font-size: 12px;
  border-radius: 4px;
  margin: 2px 8px;
}
.point-item:hover {
  background: #1e293b;
}
.point-item.selected {
  background: #4dabf722;
  border-left: 2px solid #4dabf7;
}
.pt-code {
  width: 28px;
  color: #64748b;
  font-family: monospace;
}
.pt-name {
  flex: 1;
  color: #e0e6ed;
  margin-left: 8px;
}
.pt-unit {
  color: #64748b;
  font-size: 11px;
}
.selection-bar {
  padding: 12px;
  border-top: 1px solid #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.btn-clear {
  padding: 4px 10px;
  border: 1px solid #374151;
  background: transparent;
  color: #94a3b8;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-clear:hover {
  border-color: #ef4444;
  color: #ef4444;
}
.btn-confirm {
  padding: 4px 10px;
  border: none;
  background: #4dabf7;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-confirm:hover {
  background: #3b9ed8;
}
</style>
