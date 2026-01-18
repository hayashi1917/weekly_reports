import React, { useMemo, useState } from "react";
import { Bundle, Day, Task } from "./types";

const emptyBundle: Bundle | null = null;

const toIsoLocal = (value: string) => {
  // datetime-local はローカル時刻で "YYYY-MM-DDTHH:mm" を返す。
  // UTC変換せず、入力した壁時計の値をそのまま送る。
  return value.length === 16 ? `${value}:00` : value;
};

const formatDate = (value: string) => new Date(value).toLocaleDateString();

const createTask = (day: Day, title: string, minutes: number): Task => ({
  id: `task_${Math.random().toString(36).slice(2, 8)}`,
  week_report_id: day.week_report_id,
  day_id: day.id,
  title,
  estimated_minutes: minutes,
  priority: null,
  status: "todo",
  reason_tags: [],
  note: "",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
});

export default function App() {
  const [reviewAt, setReviewAt] = useState("");
  const [bundle, setBundle] = useState<Bundle | null>(emptyBundle);
  const [selectedDayId, setSelectedDayId] = useState<string>("");
  const [taskTitle, setTaskTitle] = useState("");
  const [taskMinutes, setTaskMinutes] = useState(60);
  const [snapshot, setSnapshot] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const dayOptions = useMemo(() => bundle?.days ?? [], [bundle]);

  const handleInit = async () => {
    setError(null);
    if (!reviewAt) {
      setError("レビュー日時を入力してください。");
      return;
    }
    const response = await fetch("/api/weeks/init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_at: toIsoLocal(reviewAt) })
    });
    if (!response.ok) {
      setError("初期化に失敗しました。");
      return;
    }
    const data = (await response.json()) as Bundle;
    setBundle(data);
    setSelectedDayId(data.days[0]?.id ?? "");
    setSnapshot(null);
  };

  const handleAddTask = () => {
    if (!bundle || !selectedDayId) {
      return;
    }
    if (!taskTitle.trim()) {
      setError("タスク名を入力してください。");
      return;
    }
    const day = bundle.days.find((item) => item.id === selectedDayId);
    if (!day) {
      return;
    }
    const newTask = createTask(day, taskTitle, taskMinutes);
    setBundle({
      ...bundle,
      tasks: [...bundle.tasks, newTask]
    });
    setTaskTitle("");
    setTaskMinutes(60);
  };

  const handleFinalize = async () => {
    if (!bundle) {
      return;
    }
    const response = await fetch("/api/weeks/finalize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bundle, generate_pdf: true })
    });
    if (!response.ok) {
      setError("確定に失敗しました。");
      return;
    }
    const data = await response.json();
    setSnapshot(data.snapshot as Record<string, unknown>);
  };

  return (
    <div className="container">
      <header>
        <h1>Weekly Reports</h1>
        <p>週次レビューと次週タスクを管理するGUI</p>
      </header>

      <section className="card">
        <h2>週報の初期化</h2>
        <div className="row">
          <label>
            レビュー日時
            <input
              type="datetime-local"
              value={reviewAt}
              onChange={(event) => setReviewAt(event.target.value)}
            />
          </label>
          <button onClick={handleInit}>初期化</button>
        </div>
      </section>

      {error && <div className="error">{error}</div>}

      {bundle && (
        <section className="card">
          <h2>来週タスク</h2>
          <div className="grid">
            <div>
              <h3>タスク追加</h3>
              <label>
                日付行
                <select
                  value={selectedDayId}
                  onChange={(event) => setSelectedDayId(event.target.value)}
                >
                  {dayOptions.map((day) => (
                    <option key={day.id} value={day.id}>
                      {formatDate(day.date)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                タスク名
                <input
                  type="text"
                  value={taskTitle}
                  onChange={(event) => setTaskTitle(event.target.value)}
                />
              </label>
              <label>
                見積(分)
                <input
                  type="number"
                  min={10}
                  step={10}
                  value={taskMinutes}
                  onChange={(event) => setTaskMinutes(Number(event.target.value))}
                />
              </label>
              <button onClick={handleAddTask}>追加</button>
            </div>
            <div>
              <h3>日付行一覧</h3>
              <ul className="list">
                {bundle.days.map((day) => (
                  <li key={day.id}>
                    <strong>{formatDate(day.date)}</strong>
                    <span>タスク数: {bundle.tasks.filter((task) => task.day_id === day.id).length}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      )}

      {bundle && (
        <section className="card">
          <h2>確定・スナップショット</h2>
          <button onClick={handleFinalize}>確定して出力</button>
          {snapshot && (
            <pre className="snapshot">{JSON.stringify(snapshot, null, 2)}</pre>
          )}
        </section>
      )}
    </div>
  );
}
