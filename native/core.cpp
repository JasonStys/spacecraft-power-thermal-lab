// Original bounded power allocation and lumped thermal integration by Jason Stys.
// Functions/variables/field locations: docs/CODE_INDEX.md. No live spacecraft or battery control.
#include "core.hpp"
#include <algorithm>
#include <charconv>
#include <cmath>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace powerlab {
namespace {
// Reject nonfinite or out-of-range inputs before any numerical work.
void bound(double value, double low, double high) {
  if (!std::isfinite(value) || value < low || value > high)
    throw std::invalid_argument("range");
}
// Fully consume an ASCII numeric token; locale, NaN, infinity and trailing junk are not accepted.
double number(std::string_view value) {
  double result = 0;
  const auto parsed = std::from_chars(value.data(), value.data() + value.size(), result);
  if (parsed.ec != std::errc{} || parsed.ptr != value.data() + value.size() ||
      !std::isfinite(result))
    throw std::invalid_argument("number");
  return result;
}
// Exact small integer protocol token, rejecting floating notation and coercion.
int integer(std::string_view value) {
  int result = 0;
  const auto parsed = std::from_chars(value.data(), value.data() + value.size(), result);
  if (parsed.ec != std::errc{} || parsed.ptr != value.data() + value.size())
    throw std::invalid_argument("integer");
  return result;
}
// Bounded whitespace tokenization for one already bounded input line.
std::vector<std::string> tokens(const std::string &line) {
  std::istringstream stream(line);
  std::vector<std::string> result;
  std::string token;
  while (stream >> token)
    result.push_back(token);
  return result;
}
// Net outward radiation in watts; the separate projected solar surface is not this radiator area.
double radiation(double temperature, const Config &config) {
  constexpr double sigma = 5.670374419e-8;
  const double square = temperature * temperature;
  const double sink_square = config.sink_k * config.sink_k;
  return config.emissivity * config.radiator_area_m2 * sigma *
         (square * square - sink_square * sink_square);
}
} // namespace

void validate(const Case &input) {
  const auto &c = input.config;
  for (auto field : config_fields)
    bound(c.*field, 0, 10000);
  bound(c.solar_area_m2, 0, 1);
  bound(c.solar_efficiency, 0, 0.5);
  bound(c.battery_wh, 1, 200);
  bound(c.initial_soc, 0, 1);
  bound(c.charge_efficiency, 0.1, 1);
  bound(c.discharge_efficiency, 0.1, 1);
  bound(c.charge_limit_w, 0, 200);
  bound(c.discharge_limit_w, 0, 200);
  bound(c.heat_capacity_j_k, 1000, 10000);
  bound(c.radiator_area_m2, 0, 1);
  bound(c.emissivity, 0, 1);
  bound(c.absorptivity, 0, 1);
  bound(c.projected_area_m2, 0, 1);
  bound(c.sink_k, 0, 50);
  bound(c.external_heat_w, 0, 100);
  bound(c.base_load_w, 0, 100);
  bound(c.heater_w, 0, 100);
  bound(c.initial_temp_k, 180, 360);
  bound(c.heater_on_k, 180, 350);
  bound(c.heater_off_k, 180, 360);
  bound(c.min_temp_k, 180, 350);
  bound(c.max_temp_k, 180, 400);
  bound(c.reserve_off, 0, 1);
  bound(c.reserve_on, 0, 1);
  if (c.heater_on_k >= c.heater_off_k || c.reserve_off >= c.reserve_on ||
      c.min_temp_k >= c.max_temp_k ||
      (input.step_s != 1 && input.step_s != 5 && input.step_s != 10) || input.policy < 0 ||
      input.policy > 1 || input.heater < 0 || input.heater > 1 || input.segments.empty() ||
      input.segments.size() > 32)
    throw std::invalid_argument("settings");
  int duration = 0;
  for (const auto &segment : input.segments) {
    if (segment.duration_s < 1 || segment.duration_s > 3600)
      throw std::invalid_argument("duration");
    bound(segment.solar_flux_w_m2, 0, 2000);
    bound(segment.payload_w, 0, 150);
    duration += segment.duration_s;
  }
  if (duration > 3600)
    throw std::invalid_argument("horizon");
}

Case parse(std::string_view text) {
  if (text.empty() || text.size() > 32768)
    throw std::invalid_argument("envelope");
  std::istringstream stream{std::string(text)};
  std::string line;
  std::getline(stream, line);
  const auto header = tokens(line);
  if (header.size() != 4 || header[0] != "POWER1")
    throw std::invalid_argument("header");
  Case input;
  input.step_s = integer(header[1]);
  input.policy = integer(header[2]);
  input.heater = integer(header[3]);
  if (!std::getline(stream, line))
    throw std::invalid_argument("parameters");
  const auto parameters = tokens(line);
  if (parameters.size() != 25 || parameters[0] != "P")
    throw std::invalid_argument("parameters");
  for (std::size_t i = 0; i < config_fields.size(); ++i)
    input.config.*config_fields[i] = number(parameters[i + 1]);
  while (std::getline(stream, line)) {
    const auto fields = tokens(line);
    if (fields.size() != 4 || fields[0] != "S" || input.segments.size() >= 32)
      throw std::invalid_argument("segment");
    input.segments.push_back({integer(fields[1]), number(fields[2]), number(fields[3])});
  }
  validate(input);
  return input;
}

std::vector<Row> simulate(const Case &input) {
  validate(input);
  const auto &c = input.config;
  double energy = c.initial_soc * c.battery_wh;
  double temperature = c.initial_temp_k;
  double time = 0;
  bool heating = false;
  bool payload = true;
  std::vector<Row> rows;
  rows.reserve(3600);
  for (const auto &segment : input.segments) {
    for (int elapsed = 0; elapsed < segment.duration_s;) {
      const int seconds = std::min(input.step_s, segment.duration_s - elapsed);
      const double h = static_cast<double>(seconds);
      const double soc = energy / c.battery_wh;
      if (input.policy == 1) {
        if (soc <= c.reserve_off)
          payload = false;
        else if (soc >= c.reserve_on)
          payload = true;
      }
      if (input.heater == 1) {
        if (temperature <= c.heater_on_k)
          heating = true;
        else if (temperature >= c.heater_off_k)
          heating = false;
      }
      const double science = payload ? segment.payload_w : 0;
      const double heater = heating ? c.heater_w : 0;
      const double demand = c.base_load_w + science + heater;
      const double solar = segment.solar_flux_w_m2 * c.solar_area_m2 * c.solar_efficiency;
      const double charge =
          std::min({std::max(0.0, solar - demand), c.charge_limit_w,
                    std::max(0.0, c.battery_wh - energy) * 3600 / (c.charge_efficiency * h)});
      const double discharge = std::min({std::max(0.0, demand - solar), c.discharge_limit_w,
                                         energy * 3600 * c.discharge_efficiency / h});
      const double served = std::min(demand, solar + discharge);
      const double spill = std::max(0.0, solar - served - charge);
      const double loss =
          charge * (1 - c.charge_efficiency) + discharge * (1 / c.discharge_efficiency - 1);
      const double previous_energy = energy;
      energy = std::clamp(
          energy + (charge * c.charge_efficiency - discharge / c.discharge_efficiency) * h / 3600,
          0.0, c.battery_wh);
      const double base_served = std::min(c.base_load_w, served);
      const double heater_served = std::min(heater, std::max(0.0, served - base_served));
      const double payload_served =
          std::min(science, std::max(0.0, served - base_served - heater_served));
      const double heat = segment.solar_flux_w_m2 * c.projected_area_m2 * c.absorptivity +
                          c.external_heat_w + base_served * 0.9 + heater_served +
                          payload_served * 0.6 + loss;
      const double r1 = radiation(temperature, c);
      const double k1 = (heat - r1) / c.heat_capacity_j_k;
      const double r2 = radiation(temperature + h * k1 / 2, c);
      const double k2 = (heat - r2) / c.heat_capacity_j_k;
      const double r3 = radiation(temperature + h * k2 / 2, c);
      const double k3 = (heat - r3) / c.heat_capacity_j_k;
      const double r4 = radiation(temperature + h * k3, c);
      const double k4 = (heat - r4) / c.heat_capacity_j_k;
      const double radiated = (r1 + 2 * r2 + 2 * r3 + r4) / 6;
      const double previous_temperature = temperature;
      temperature += h * (k1 + 2 * k2 + 2 * k3 + k4) / 6;
      if (!std::isfinite(temperature) || temperature < 100 || temperature > 450)
        throw std::invalid_argument("numerical domain");
      const double electric_residual =
          solar - served - spill - loss - (energy - previous_energy) * 3600 / h;
      const double thermal_residual =
          heat - radiated - c.heat_capacity_j_k * (temperature - previous_temperature) / h;
      time += h;
      rows.push_back({time,
                      h,
                      solar,
                      demand,
                      served,
                      demand - served,
                      charge,
                      discharge,
                      loss,
                      spill,
                      energy,
                      temperature,
                      heat,
                      radiated,
                      electric_residual,
                      thermal_residual,
                      base_served,
                      heater_served,
                      payload_served,
                      segment.payload_w - science,
                      static_cast<double>(heating),
                      static_cast<double>(payload),
                      segment.solar_flux_w_m2,
                      science});
      elapsed += seconds;
    }
  }
  return rows;
}

std::string json(const std::vector<Row> &rows) {
  std::ostringstream output;
  output << std::setprecision(17) << "[";
  bool comma = false;
  for (const auto &row : rows) {
    if (comma)
      output << ',';
    comma = true;
    output << '{';
    for (std::size_t i = 0; i < columns.size(); ++i) {
      if (i)
        output << ',';
      output << '"' << columns[i] << "\":" << row[i];
    }
    output << '}';
  }
  output << "]\n";
  return output.str();
}
} // namespace powerlab
