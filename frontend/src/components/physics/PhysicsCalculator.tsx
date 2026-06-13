import React, { useCallback, useMemo, useState } from 'react';
import { FormulaMarkdown } from '../common/FormulaMarkdown';
import { PHYSICS_CATALOG, findDefaultLeaf, findLeaf } from '../../physics/catalog';
import { PhysicsPanelRouter } from '../../physics/PhysicsPanelRouter';
import './PhysicsCalculator.css';

export const PhysicsCalculator: React.FC = () => {
  const defaultLeaf = useMemo(() => findDefaultLeaf(), []);
  const [categoryId, setCategoryId] = useState(defaultLeaf.categoryId);
  const [typeId, setTypeId] = useState(defaultLeaf.typeId);
  const [subtypeId, setSubtypeId] = useState(defaultLeaf.subtypeId);
  const [searchQuery, setSearchQuery] = useState('');

  const leaf = useMemo(() => findLeaf(categoryId, typeId, subtypeId) ?? defaultLeaf, [categoryId, typeId, subtypeId, defaultLeaf]);

  const category = PHYSICS_CATALOG.find((c) => c.id === categoryId) ?? PHYSICS_CATALOG[0];
  const type = category.types.find((t) => t.id === typeId) ?? category.types[0];
  const availableTypes = category.types;
  const availableSubtypes = type?.subtypes ?? [];

  const selectCategory = useCallback((id: string) => {
    setCategoryId(id);
    const c = PHYSICS_CATALOG.find((x) => x.id === id);
    if (!c?.types.length) return;
    const t0 = c.types[0];
    setTypeId(t0.id);
    setSubtypeId(t0.subtypes[0]?.id ?? '');
  }, []);

  const selectType = useCallback(
    (catId: string, tid: string) => {
      setCategoryId(catId);
      setTypeId(tid);
      const c = PHYSICS_CATALOG.find((x) => x.id === catId);
      const t = c?.types.find((x) => x.id === tid);
      if (t?.subtypes[0]) setSubtypeId(t.subtypes[0].id);
    },
    []
  );

  const selectSubtype = useCallback((sid: string) => {
    setSubtypeId(sid);
  }, []);

  const searchIndex = useMemo(
    () =>
      PHYSICS_CATALOG.flatMap((c) =>
        c.types.flatMap((t) =>
          t.subtypes.map((s) => ({
            categoryId: c.id,
            categoryLabel: c.label,
            typeId: t.id,
            typeLabel: t.label,
            subtypeId: s.id,
            subtypeLabel: s.label,
            panelId: s.panelId,
            searchText: `${c.label} ${t.label} ${s.label} ${s.panelId}`.toLowerCase(),
          }))
        )
      ),
    []
  );

  const searchResults = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return [];
    return searchIndex.filter((entry) => entry.searchText.includes(q)).slice(0, 8);
  }, [searchIndex, searchQuery]);

  const jumpToLeaf = useCallback((entry: (typeof searchIndex)[number]) => {
    setCategoryId(entry.categoryId);
    setTypeId(entry.typeId);
    setSubtypeId(entry.subtypeId);
    setSearchQuery('');
  }, []);

  const onSearchKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
    if (e.key === 'Enter' && searchResults[0]) {
      e.preventDefault();
      jumpToLeaf(searchResults[0]);
    }
  };

  return (
    <div className="physics-calculator physics-calculator-layout">
      <header className="physics-calculator-header">
        <h2>Physics calculators</h2>
        <FormulaMarkdown className="physics-calculator-lead">
          {`Textbook and empirical RF relations: resonance, impedance match ($|S_{11}|$, $\\Gamma$), gain, arrays, and link budget. Use **Section → Type → Subtype**. Validate critical designs with full-wave tools and measurement.`}
        </FormulaMarkdown>
      </header>

      <div className="physics-layout-two-pane">
        <aside className="physics-control-panel" aria-label="Calculator selection panel">
          <div className="physics-search-wrap">
            <input
              type="search"
              className="physics-search-input"
              placeholder="Search calculator (e.g., dipole, Friis, patch, phased array)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={onSearchKeyDown}
              aria-label="Search physics calculators"
            />
            {searchQuery.trim() && (
              <div className="physics-search-results" role="listbox" aria-label="Matching calculators">
                {searchResults.length ? (
                  searchResults.map((entry) => (
                    <button
                      key={`${entry.categoryId}-${entry.typeId}-${entry.subtypeId}`}
                      type="button"
                      className="physics-search-item"
                      onClick={() => jumpToLeaf(entry)}
                    >
                      <span className="physics-search-item-sub">{entry.subtypeLabel}</span>
                      <span className="physics-search-item-path">{entry.categoryLabel} / {entry.typeLabel}</span>
                    </button>
                  ))
                ) : (
                  <div className="physics-search-empty">No matching calculator found.</div>
                )}
              </div>
            )}
          </div>

          <h3 className="physics-control-title">Calculator selector</h3>
          <p className="physics-control-caption">Pick one option per step to open a focused calculator.</p>

          <label className="physics-select-label" htmlFor="physics-section-select">
            Section
          </label>
          <select
            id="physics-section-select"
            className="physics-select"
            value={categoryId}
            onChange={(e) => selectCategory(e.target.value)}
          >
            {PHYSICS_CATALOG.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>

          <label className="physics-select-label" htmlFor="physics-type-select">
            Type
          </label>
          <select
            id="physics-type-select"
            className="physics-select"
            value={typeId}
            onChange={(e) => selectType(category.id, e.target.value)}
          >
            {availableTypes.map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
          </select>

          <label className="physics-select-label" htmlFor="physics-subtype-select">
            Subtype
          </label>
          <select
            id="physics-subtype-select"
            className="physics-select"
            value={subtypeId}
            onChange={(e) => selectSubtype(e.target.value)}
          >
            {availableSubtypes.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>

          <div className="physics-current-selection">
            <div className="physics-nav-title">Current</div>
            <div className="physics-current-line">{category.label}</div>
            <div className="physics-current-line">{type.label}</div>
            <div className="physics-current-line physics-current-leaf">{leaf.subtypeLabel}</div>
          </div>
        </aside>

        <div className="physics-main-panel">
          <p className="physics-category-desc">{category.description}</p>
          <PhysicsPanelRouter leaf={leaf} />
        </div>
      </div>
    </div>
  );
};
