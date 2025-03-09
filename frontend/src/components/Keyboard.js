import React from "react";

const Keyboard = () => {
  return (
    <div className="grid grid-cols-3 gap-4">
      {Array.from({ length: 9 }, (_, i) => i + 1).map((num) => (
        <button
          key={num}
          className="p-4 bg-blue-500 text-white text-xl rounded"
        >
          {num}
        </button>
      ))}
    </div>
  );
};

export default Keyboard;
