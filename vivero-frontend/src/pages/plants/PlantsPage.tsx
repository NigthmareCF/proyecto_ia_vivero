import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getPlants } from "../../api/plantsApi";

type PlantRecord = {
  id?: string | number;
  name?: string;
  qrCode?: string;
  plantGroupCode?: string;
  location?: string;
  status?: string;
  estadoGeneral?: string;
  evidenceCount?: number;
  lastObservedAt?: string;
};

function plantKey(plant: PlantRecord) {
  return String(plant.id ?? plant.qrCode ?? plant.plantGroupCode ?? plant.name ?? "planta");
}

function plantTitle(plant: PlantRecord) {
  return plant.name ?? plant.plantGroupCode ?? plant.qrCode ?? `Planta ${plantKey(plant)}`;
}

function plantStatus(plant: PlantRecord) {
  return plant.status ?? plant.estadoGeneral ?? "SIN_ANALISIS";
}

export function PlantsPage() {
  const [plants, setPlants] = useState<PlantRecord[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    getPlants().then(setPlants).catch(() => setPlants([]));
  }, []);

  const normalizedSearch = search.trim().toUpperCase();
  const visiblePlants = plants.filter((plant) => {
    if (!normalizedSearch) return true;
    return [plant.name, plant.qrCode, plant.plantGroupCode, plant.location]
      .filter(Boolean)
      .some((value) => String(value).toUpperCase().includes(normalizedSearch));
  });

  return (
    <section className="space-y-6">
      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Inventario operativo</p>
            <h2 className="mt-2 font-display text-3xl text-ink">Plantas</h2>
            <p className="mt-2 max-w-2xl text-sm text-moss">
              Vista agrupada por planta/maceta. El reporte general se consolida con las evidencias que llegan desde patrullaje.
            </p>
          </div>
          <input
            className="w-full rounded-2xl border border-ink/10 px-4 py-3 text-sm outline-none transition focus:border-clay lg:max-w-sm"
            placeholder="Buscar por QR, planta o ubicacion"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <article className="rounded-[1.5rem] bg-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Registradas</p>
            <p className="mt-2 font-display text-4xl text-ink">{plants.length}</p>
          </article>
          <article className="rounded-[1.5rem] bg-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Con evidencia</p>
            <p className="mt-2 font-display text-4xl text-ink">
              {plants.filter((plant) => Number(plant.evidenceCount ?? 0) > 0).length}
            </p>
          </article>
          <article className="rounded-[1.5rem] bg-sand p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-moss">Filtradas</p>
            <p className="mt-2 font-display text-4xl text-ink">{visiblePlants.length}</p>
          </article>
        </div>
      </article>

      <article className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h3 className="font-display text-2xl text-ink">Plantas y macetas</h3>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          {visiblePlants.length > 0 ? (
            visiblePlants.map((plant) => (
              <Link
                key={plantKey(plant)}
                to={`/plants/${encodeURIComponent(plantKey(plant))}`}
                className="rounded-[1.5rem] border border-sand p-4 transition hover:border-clay"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-sand px-3 py-1 text-sm text-ink">{plantTitle(plant)}</span>
                  <span className="rounded-full bg-sand px-3 py-1 text-sm text-ink">{plantStatus(plant)}</span>
                </div>
                <p className="mt-3 text-sm text-moss">{plant.location ?? "Sin ubicacion registrada"}</p>
                <p className="mt-2 text-xs uppercase tracking-[0.18em] text-moss">
                  {plant.qrCode ?? plant.plantGroupCode ?? "QR pendiente"} · {plant.evidenceCount ?? 0} evidencias
                </p>
              </Link>
            ))
          ) : (
            <p className="text-sm text-moss">
              Aun no hay plantas disponibles desde el backend. Cuando el robot cierre un patrullaje, esta vista puede mostrar los grupos planta/maceta consolidados.
            </p>
          )}
        </div>
      </article>
    </section>
  );
}
