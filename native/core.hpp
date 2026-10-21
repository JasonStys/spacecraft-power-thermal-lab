// Coupled finite educational model by Jason Stys; fields/functions: docs/CODE_INDEX.md.
// SI seconds, watts, joules and kelvin; chemical battery energy is watt-hours. No device I/O.
#pragma once
#include <array>
#include <string>
#include <string_view>
#include <vector>

namespace powerlab {
// Invented constant parameters, validated before simulation; no electrochemistry or real geometry.
struct Config {
  double solar_area_m2 = 0.2;
  double solar_efficiency = 0.28;
  double battery_wh = 40;
  double initial_soc = 0.6;
  double charge_efficiency = 0.9;
  double discharge_efficiency = 0.9;
  double charge_limit_w = 30;
  double discharge_limit_w = 40;
  double heat_capacity_j_k = 5000;
  double radiator_area_m2 = 0.08;
  double emissivity = 0.8;
  double absorptivity = 0.2;
  double projected_area_m2 = 0.05;
  double sink_k = 3;
  double external_heat_w = 5;
  double base_load_w = 8;
  double heater_w = 6;
  double heater_on_k = 275;
  double heater_off_k = 280;
  double reserve_off = 0.3;
  double reserve_on = 0.5;
  double initial_temp_k = 285;
  double min_temp_k = 260;
  double max_temp_k = 320;
};
// Piecewise-constant illumination and requested scientific payload, not predicted orbital geometry.
struct Segment {
  int duration_s;
  double solar_flux_w_m2;
  double payload_w;
};
// Finite controls and at most 32 segments/3600 seconds; step clipped at segment boundaries.
struct Case {
  Config config;
  int step_s = 5;
  int policy = 0;
  int heater = 1;
  std::vector<Segment> segments;
};
inline constexpr std::array<double Config::*, 24> config_fields = {
    &Config::solar_area_m2,     &Config::solar_efficiency,
    &Config::battery_wh,        &Config::initial_soc,
    &Config::charge_efficiency, &Config::discharge_efficiency,
    &Config::charge_limit_w,    &Config::discharge_limit_w,
    &Config::heat_capacity_j_k, &Config::radiator_area_m2,
    &Config::emissivity,        &Config::absorptivity,
    &Config::projected_area_m2, &Config::sink_k,
    &Config::external_heat_w,   &Config::base_load_w,
    &Config::heater_w,          &Config::heater_on_k,
    &Config::heater_off_k,      &Config::reserve_off,
    &Config::reserve_on,        &Config::initial_temp_k,
    &Config::min_temp_k,        &Config::max_temp_k};
// Numeric-only fixed result schema, interval averages ending at time_s; flags are 0/1.
inline constexpr std::array<std::string_view, 24> columns = {"time_s",
                                                             "dt_s",
                                                             "solar_w",
                                                             "requested_w",
                                                             "served_w",
                                                             "unserved_w",
                                                             "charge_in_w",
                                                             "discharge_bus_w",
                                                             "battery_loss_w",
                                                             "spill_w",
                                                             "energy_wh",
                                                             "temperature_k",
                                                             "heat_in_w",
                                                             "radiation_w",
                                                             "electric_residual_w",
                                                             "thermal_residual_w",
                                                             "base_served_w",
                                                             "heater_served_w",
                                                             "payload_served_w",
                                                             "shed_requested_w",
                                                             "heater_on",
                                                             "payload_enabled",
                                                             "solar_flux_w_m2",
                                                             "payload_requested_w"};
using Row = std::array<double, 24>;
// Validate all numerical domains, finite controls, hysteresis order and total workload.
void validate(const Case &input);
// Parse a complete bounded POWER1/P/S envelope; never reflect arbitrary text into output.
Case parse(std::string_view text);
// Simulate bounded average electrical flows and an RK4 single-node thermal response.
std::vector<Row> simulate(const Case &input);
// Serialize only fixed numeric keys after a complete successful simulation.
std::string json(const std::vector<Row> &rows);
} // namespace powerlab
