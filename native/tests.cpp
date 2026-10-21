// Hand-derived and hostile-envelope native contracts by Jason Stys; index: docs/CODE_INDEX.md.
// Functions exercise SI energy, saturation, allocation, hysteresis and analytic thermal responses.
#include "core.hpp"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>

namespace {
// Fail even in Release builds; never use disabled NDEBUG assertions as the test gate.
void require(bool condition) {
  if (!condition)
    throw std::runtime_error("native contract failed");
}
// Compare a computed quantity with a hand-derived value using an explicit absolute tolerance.
void near(double value, double expected, double tolerance = 1e-8) {
  require(std::abs(value - expected) <= tolerance);
}
// A minimal dark adiabatic body isolates battery behavior from radiation and heater controls.
powerlab::Case simple() {
  powerlab::Case input;
  input.config.emissivity = 0;
  input.config.external_heat_w = 0;
  input.config.base_load_w = 10;
  input.config.solar_area_m2 = 0;
  input.config.battery_wh = 20;
  input.config.initial_soc = 0.5;
  input.config.discharge_efficiency = 0.5;
  input.heater = 0;
  input.segments = {{360, 0, 0}};
  return input;
}
// Battery watt-hours follow a closed-form dark-load case; both energy ledgers close independently.
void discharge_contract() {
  const auto input = simple();
  const auto rows = powerlab::simulate(input);
  near(rows.back()[10], 8);
  for (const auto &row : rows) {
    near(row[14], 0);
    near(row[15], 0);
  }
}
// Empty/full batteries saturate without negative energy, invented supply, or lost surplus.
void saturation_contract() {
  auto input = simple();
  input.config.initial_soc = 0;
  auto rows = powerlab::simulate(input);
  near(rows.back()[10], 0);
  near(rows.back()[5], 10);
  input.config.initial_soc = 1;
  input.config.solar_area_m2 = 0.2;
  input.segments = {{20, 1000, 0}};
  rows = powerlab::simulate(input);
  near(rows.back()[10], 20);
  require(rows.back()[9] > 0);
}
// A zero-emissivity constant-heat body follows C*dT=Q*dt exactly.
void adiabatic_contract() {
  auto input = simple();
  input.config.base_load_w = 0;
  input.config.external_heat_w = 10;
  input.config.heat_capacity_j_k = 1000;
  input.segments = {{100, 0, 0}};
  const auto rows = powerlab::simulate(input);
  near(rows.back()[11], 286);
}
// Radiation-only cooling to a zero-kelvin ideal sink has a separable analytic reference solution.
void radiation_contract() {
  auto input = simple();
  input.config.base_load_w = 0;
  input.config.emissivity = 0.8;
  input.config.radiator_area_m2 = 0.1;
  input.config.heat_capacity_j_k = 1000;
  input.config.initial_temp_k = 350;
  input.config.sink_k = 0;
  input.segments = {{600, 0, 0}};
  const double exact =
      std::pow(std::pow(350.0, -3) + 3 * 0.8 * 0.1 * 5.670374419e-8 * 600 / 1000, -1.0 / 3);
  input.step_s = 10;
  const double coarse = powerlab::simulate(input).back()[11];
  input.step_s = 1;
  const double fine = powerlab::simulate(input).back()[11];
  near(coarse, exact, 1e-5);
  require(std::abs(fine - exact) < std::abs(coarse - exact));
}
// Under constrained power, housekeeping precedes heater and then scientific payload.
void priority_contract() {
  auto input = simple();
  input.config.initial_soc = 0;
  input.config.base_load_w = 8;
  input.config.solar_area_m2 = 0.2;
  input.config.initial_temp_k = 250;
  input.heater = 1;
  input.segments = {{10, 200, 15}};
  const auto row = powerlab::simulate(input).front();
  near(row[16], 8);
  near(row[17], 3.2);
  near(row[18], 0);
  require(row[20] == 1);
}
// Reserve hysteresis sheds science below its off threshold without discarding housekeeping.
void reserve_contract() {
  auto input = simple();
  input.policy = 1;
  input.config.initial_soc = 0.2;
  input.segments = {{10, 0, 50}};
  const auto row = powerlab::simulate(input).front();
  near(row[21], 0);
  near(row[19], 50);
  near(row[16], 10);
}
// Invalid values and bounded malformed byte strings fail before successful evidence exists.
void rejection_contract() {
  auto input = simple();
  input.config.battery_wh = std::numeric_limits<double>::quiet_NaN();
  bool rejected = false;
  try {
    powerlab::simulate(input);
  } catch (const std::invalid_argument &) {
    rejected = true;
  }
  require(rejected);
  for (int size = 0; size <= 1024; ++size) {
    rejected = false;
    try {
      powerlab::parse(std::string(static_cast<std::size_t>(size), static_cast<char>(size % 256)));
    } catch (const std::invalid_argument &) {
      rejected = true;
    }
    require(rejected);
  }
}
} // namespace
// Execute seven named native contracts; a single failed assertion exits nonzero in every build
// mode.
int main() {
  try {
    discharge_contract();
    saturation_contract();
    adiabatic_contract();
    radiation_contract();
    priority_contract();
    reserve_contract();
    rejection_contract();
    std::cout << "Seven native contract groups passed\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
