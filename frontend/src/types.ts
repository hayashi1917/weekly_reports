export type Issue = {
  problem: string;
  root_cause: string;
  improvement: string;
  tags: string[];
};

export type WeekReport = {
  id: string;
  week_id: string;
  cycle_start: string;
  cycle_end: string;
  review_at: string;
  status: string;
  prev_week_report_id?: string | null;
  goals_week: string[];
  goals_month: string[];
  goals_long: string[];
  good_points: string[];
  issues: Issue[];
  created_at?: string | null;
  updated_at?: string | null;
};

export type Day = {
  id: string;
  week_report_id: string;
  date: string;
  available_minutes?: number | null;
  planned_minutes?: number | null;
  scheduled_minutes?: number | null;
  done_count?: number | null;
  total_count?: number | null;
};

export type Task = {
  id: string;
  week_report_id: string;
  day_id: string;
  title: string;
  estimated_minutes: number;
  priority?: number | null;
  status: string;
  reason_tags: string[];
  note?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type TaskSession = {
  id: string;
  task_id: string;
  start_at: string;
  end_at: string;
  note?: string | null;
  is_completed?: boolean | null;
};

export type Bundle = {
  week_report: WeekReport;
  days: Day[];
  tasks: Task[];
  task_sessions: TaskSession[];
  last_week_tasks: Task[];
};
