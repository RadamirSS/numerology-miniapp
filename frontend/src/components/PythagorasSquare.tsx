import React from "react";

export interface PythagorasSquareProps {
  /**
   * Массив из 9 значений для ячеек квадрата.
   * Порядок:
   * [0] [1] [2]  ->  1  4  7
   * [3] [4] [5]  ->  2  5  8
   * [6] [7] [8]  ->  3  6  9
   */
  cells: (string | null | undefined)[];
}

export const PythagorasSquare: React.FC<PythagorasSquareProps> = ({ cells }) => {
  // Гарантируем, что всегда 9 элементов
  const safeCells =
    Array.isArray(cells) && cells.length === 9 ? cells : Array(9).fill(null);

  return (
    <div className="pythagoras-square">
      {safeCells.map((value, index) => {
        const text =
          value && value.toString().trim().length > 0
            ? value.toString().trim()
            : "–";
        return (
          <div key={index} className="pythagoras-square__cell">
            {text}
          </div>
        );
      })}
    </div>
  );
};

