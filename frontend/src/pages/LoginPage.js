import React from "react";
import Keyboard from "../components/Keyboard";

const LoginPage = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-200">
      <h1 className="text-3xl font-bold mb-6">Teclado Virtual Seguro</h1>
      <Keyboard />
    </div>
  );
};

export default LoginPage;