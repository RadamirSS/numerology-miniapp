import { useState } from "react";
import "./theme.css";
import MatrixPage from "./pages/MatrixPage";
import CalculatorsPage from "./pages/CalculatorsPage";
import ProfilePage from "./pages/ProfilePage";
import AiInterpretationPage from "./pages/AiInterpretationPage";

type Tab = "matrix" | "calculators" | "ai" | "profile";

export interface MatrixState {
  date: string;
  imageUrl: string | null;
  error: string | null;
  loading: boolean;
  digitInterpretations: Record<string, string> | null; // ключи "1".."9"
}

export interface CalcState {
  date: string;
  currentCalc: string;
  html: string;
  error: string | null;
  loading: boolean;
}

export interface AiState {
  birthDate: string;
  report: string | null;
  profile: any | null;
  loading: boolean;
  error: string | null;
}

export interface UserInfo {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  birth_date: string;
  tariff: string | null;
  telegram_id: number | null;
  telegram_username: string | null;
  telegram_first_name: string | null;
  telegram_last_name: string | null;
  is_email_verified: boolean;
}


function App() {
  const [tab, setTab] = useState<Tab>("matrix");
  const [currentUser, setCurrentUser] = useState<UserInfo | null>(null);

  const [matrixState, setMatrixState] = useState<MatrixState>({
    date: "",
    imageUrl: null,
    error: null,
    loading: false,
    digitInterpretations: null,
  });

  const [calcState, setCalcState] = useState<CalcState>({
    date: "",
    currentCalc: "money_code",
    html: "",
    error: null,
    loading: false,
  });

  const [aiState, setAiState] = useState<AiState>({
    birthDate: "",
    report: null,
    profile: null,
    loading: false,
    error: null,
  });

  return (
    <div className="app-root">
      {/* Шапка приложения */}
      <div className="app-header">
        <h1 className="app-title">Numerolog Mini App</h1>
        <div className="app-user-pill">
          {currentUser ? `👤 ${currentUser.name}` : "Гость"}
        </div>
      </div>

      <div style={{ padding: 16, paddingBottom: 72 }}>
        {tab === "matrix" && (
          <MatrixPage state={matrixState} setState={setMatrixState} />
        )}
        {tab === "calculators" && (
          <CalculatorsPage state={calcState} setState={setCalcState} />
        )}
        {tab === "ai" && (
          <AiInterpretationPage state={aiState} setState={setAiState} />
        )}
        {tab === "profile" && (
          <ProfilePage currentUser={currentUser} setCurrentUser={setCurrentUser} />
        )}
      </div>

      <div className="tabbar">
        <button
          className={tab === "matrix" ? "active" : ""}
          onClick={() => setTab("matrix")}
        >
          Матрица
        </button>
        <button
          className={tab === "calculators" ? "active" : ""}
          onClick={() => setTab("calculators")}
        >
          Калькуляторы
        </button>
        <button
          className={tab === "ai" ? "active" : ""}
          onClick={() => setTab("ai")}
        >
          AI интерпретация
        </button>
        <button
          className={tab === "profile" ? "active" : ""}
          onClick={() => setTab("profile")}
        >
          Личный кабинет
        </button>
      </div>
    </div>
  );
}

export default App;
