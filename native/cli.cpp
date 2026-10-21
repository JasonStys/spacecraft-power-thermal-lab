// Fixed stdin-only simulation worker by Jason Stys; run/main/bytes: docs/CODE_INDEX.md.
// Complete bounded parsing and numerical work must succeed before any stdout is emitted.
#include "core.hpp"
#include <iostream>
#include <stdexcept>

// Read a finite envelope, validate all rows, then emit one complete successful result.
int main(int argc, char **) {
  try {
    if (argc != 1)
      throw std::invalid_argument("arguments");
    std::string bytes;
    char value = 0;
    while (std::cin.get(value)) {
      if (bytes.size() >= 32768)
        throw std::invalid_argument("size");
      bytes.push_back(value);
    }
    const auto input = powerlab::parse(bytes);
    const auto rows = powerlab::simulate(input);
    const auto result = powerlab::json(rows);
    std::cout << result;
    return 0;
  } catch (const std::exception &) {
    std::cerr << "Invalid bounded power-thermal case\n";
    return 2;
  }
}
