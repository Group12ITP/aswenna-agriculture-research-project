import React, { useState, useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Calculator, Sparkles, AlertCircle, Calendar, DollarSign, History, AlertTriangle } from 'lucide-react';
import type { MetadataResponse, DefaultsResponse, PredictionRequest } from '../../types/api';
import { useCropDistrictMatrix } from '../../hooks/useCropDistrictMatrix';
import { getNextSeasonLabel } from '../../lib/format';

interface PredictionFormProps {
  metadata?: MetadataResponse;
  defaults?: DefaultsResponse;
  isLoading: boolean;
  onSubmit: (data: PredictionRequest) => void;
}

const formSchema = z.object({
  district: z.string().min(1, 'Please select an administrative district'),
  crop: z.string().min(1, 'Please select an agricultural crop'),
  season: z.enum(['Maha', 'Yala']),
  irrigation_type: z.enum(['Irrigated', 'Rainfed', 'Unspecified']),
  usd_lkr_rate: z.number().min(50.0, 'Rate must be >= 50.0 LKR/USD').max(1000.0, 'Rate must be <= 1000.0 LKR/USD'),
  prev_season_cost: z.union([
    z.number().min(0, 'Cost must be >= 0'),
    z.null(),
    z.undefined(),
    z.literal('').transform(() => null),
    z.string().refine((val) => val === '' || (!isNaN(Number(val)) && Number(val) >= 0), {
      message: 'Cost must be a positive number',
    }),
  ]).optional(),
});

interface FormValues {
  district: string;
  crop: string;
  season: 'Maha' | 'Yala';
  irrigation_type: 'Irrigated' | 'Rainfed' | 'Unspecified';
  usd_lkr_rate: number;
  prev_season_cost?: number | string | null;
}

export const PredictionForm: React.FC<PredictionFormProps> = ({
  metadata,
  defaults,
  isLoading,
  onSubmit,
}) => {
  const { data: matrix } = useCropDistrictMatrix();
  const nextSeasonLabel = useMemo(() => getNextSeasonLabel(), []);
  const referenceYear = defaults?.reference_year || 2025;
  const defaultUsdRate = defaults?.usd_lkr_rate_default || 300.73;

  // Toggle state to permit national extrapolation
  const [showAllCrops, setShowAllCrops] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema) as any,
    defaultValues: {
      district: 'Anuradhapura',
      crop: 'Paddy',
      season: 'Maha',
      irrigation_type: 'Irrigated',
      usd_lkr_rate: defaultUsdRate,
      prev_season_cost: '',
    },
  });

  const selectedDistrict = watch('district');
  const selectedCrop = watch('crop');
  const selectedSeason = watch('season');
  const selectedIrrigation = watch('irrigation_type');
  const watchedCost = watch('prev_season_cost');

  // Districts list derived from matrix or metadata
  const allDistricts = useMemo(() => {
    return matrix?.all_districts || metadata?.districts_supported || ['Anuradhapura'];
  }, [matrix, metadata]);

  // Valid crops with historical empirical survey data for the selected district
  const districtCropsMap = useMemo(() => {
    if (!matrix?.districts || !selectedDistrict) return {};
    return matrix.districts[selectedDistrict]?.crops || {};
  }, [matrix, selectedDistrict]);

  const validDistrictCrops = useMemo(() => {
    return Object.keys(districtCropsMap);
  }, [districtCropsMap]);

  const allCropsList = useMemo(() => {
    return matrix?.all_crops || metadata?.crops_supported || [];
  }, [matrix, metadata]);

  // Determine if currently selected crop is an unobserved cold-start pair
  const isColdStartCrop = Boolean(
    selectedCrop && selectedDistrict && !validDistrictCrops.includes(selectedCrop)
  );

  // Available irrigation types for current (district, crop)
  const availableIrrigation = useMemo(() => {
    const cropInfo = districtCropsMap[selectedCrop];
    if (cropInfo?.irrigation_types?.length) {
      return cropInfo.irrigation_types;
    }
    return ['Irrigated', 'Rainfed', 'Unspecified'] as const;
  }, [districtCropsMap, selectedCrop]);

  // Available seasons for current (district, crop)
  const availableSeasons = useMemo(() => {
    const cropInfo = districtCropsMap[selectedCrop];
    if (cropInfo?.seasons?.length) {
      return cropInfo.seasons;
    }
    return ['Maha', 'Yala'] as const;
  }, [districtCropsMap, selectedCrop]);

  // Initial population of default values
  useEffect(() => {
    if (defaults?.usd_lkr_rate_default) {
      setValue('usd_lkr_rate', defaults.usd_lkr_rate_default);
    }
  }, [defaults, setValue]);

  // Auto-fill prev_season_cost lookup
  const lookupKey = `${selectedCrop}|${selectedDistrict}|${selectedIrrigation}`;
  const autoFilledCost = defaults?.latest_available_costs?.[lookupKey];

  useEffect(() => {
    if (defaults?.latest_available_costs) {
      if (autoFilledCost !== undefined) {
        setValue('prev_season_cost', autoFilledCost);
      } else {
        setValue('prev_season_cost', '');
      }
    }
  }, [selectedCrop, selectedDistrict, selectedIrrigation, defaults, autoFilledCost, setValue]);

  // Ensure season & irrigation stay valid when available options change
  useEffect(() => {
    if (availableSeasons.length > 0 && !availableSeasons.includes(selectedSeason as any)) {
      setValue('season', availableSeasons[0]);
    }
    if (availableIrrigation.length > 0 && !availableIrrigation.includes(selectedIrrigation as any)) {
      setValue('irrigation_type', availableIrrigation[0]);
    }
  }, [availableSeasons, availableIrrigation, selectedSeason, selectedIrrigation, setValue]);

  // Handle District selection with confirmation if user already chose a crop
  const handleDistrictChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextDistrict = e.target.value;
    if (selectedCrop) {
      const ok = window.confirm('Changing district will reset your crop selection. Continue?');
      if (!ok) {
        e.target.value = selectedDistrict;
        return;
      }
    }

    setValue('district', nextDistrict);
    // Reset Crop, Season, Irrigation
    const nextDistrictCrops = matrix?.districts?.[nextDistrict]?.crops || {};
    const validNextCrops = Object.keys(nextDistrictCrops);

    if (validNextCrops.length > 0 && !showAllCrops) {
      const defaultNextCrop = validNextCrops[0];
      setValue('crop', defaultNextCrop);
      const cropInfo = nextDistrictCrops[defaultNextCrop];
      if (cropInfo?.seasons?.length) setValue('season', cropInfo.seasons[0]);
      if (cropInfo?.irrigation_types?.length) setValue('irrigation_type', cropInfo.irrigation_types[0]);
    } else {
      setValue('crop', '');
    }
  };

  // Handle Crop selection change
  const handleCropChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const nextCrop = e.target.value;
    setValue('crop', nextCrop);
    const cropInfo = districtCropsMap[nextCrop];
    if (cropInfo?.seasons?.length) {
      setValue('season', cropInfo.seasons[0]);
    }
    if (cropInfo?.irrigation_types?.length) {
      setValue('irrigation_type', cropInfo.irrigation_types[0]);
    }
  };

  const isCostEmpty =
    watchedCost === '' || watchedCost === null || watchedCost === undefined;
  const isAutoFilledMatch =
    !isCostEmpty && autoFilledCost !== undefined && Number(watchedCost) === autoFilledCost;

  const onFormSubmit = (data: FormValues) => {
    const rawCost = data.prev_season_cost;
    const normalizedCost =
      rawCost === '' || rawCost === undefined || rawCost === null
        ? null
        : Number(rawCost);

    onSubmit({
      district: data.district,
      crop: data.crop,
      season: data.season,
      irrigation_type: data.irrigation_type,
      reference_year: referenceYear,
      usd_lkr_rate: Number(data.usd_lkr_rate),
      prev_season_cost:
        normalizedCost !== null && !isNaN(normalizedCost) && normalizedCost >= 0
          ? normalizedCost
          : null,
      allow_extrapolation: showAllCrops,
    });
  };

  return (
    <div className="bg-white rounded-2xl p-6 sm:p-7 border border-slate-200/80 shadow-xs">
      {/* Target Planning Horizon Display Row */}
      <div className="mb-5 p-3.5 rounded-xl bg-emerald-50/90 border border-emerald-200/90 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-emerald-950 shadow-xs">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-emerald-700 shrink-0" />
          <span>
            Predicting for: <span className="font-extrabold text-emerald-900">{nextSeasonLabel}</span>
          </span>
        </div>
        <span className="self-start sm:self-auto px-2.5 py-0.5 rounded-full bg-emerald-200/60 font-mono text-[11px] font-bold text-emerald-900 border border-emerald-300">
          Using {referenceYear} reference data
        </span>
      </div>

      <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Calculator className="w-5 h-5 text-emerald-600" />
            <span>Cultivation Parameters</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure target agronomic scenario. Model projects forward from latest reference baselines.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-5">
        {/* District & Crop Row (Cascading & Mutually Filtered) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* District Dropdown */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              District / Region <span className="text-emerald-600">*</span>
            </label>
            <select
              value={selectedDistrict || ''}
              onChange={handleDistrictChange}
              className={`w-full px-3.5 py-2.5 rounded-xl border text-sm bg-white focus:outline-none focus:ring-2 transition-all ${
                errors.district
                  ? 'border-rose-300 focus:ring-rose-500/20'
                  : 'border-slate-300 focus:border-emerald-500 focus:ring-emerald-500/20'
              }`}
            >
              {allDistricts.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            {errors.district && (
              <p className="text-rose-600 text-[11px] mt-1 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.district.message}
              </p>
            )}
          </div>

          {/* Crop Dropdown (Filtered by District) */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Target Crop <span className="text-emerald-600">*</span>
            </label>
            <select
              value={selectedCrop || ''}
              onChange={handleCropChange}
              className={`w-full px-3.5 py-2.5 rounded-xl border text-sm bg-white focus:outline-none focus:ring-2 transition-all ${
                errors.crop
                  ? 'border-rose-300 focus:ring-rose-500/20'
                  : isColdStartCrop
                  ? 'border-amber-300 focus:border-amber-500 focus:ring-amber-500/20 bg-amber-50/20'
                  : 'border-slate-300 focus:border-emerald-500 focus:ring-emerald-500/20'
              }`}
            >
              <option value="" disabled>
                {validDistrictCrops.length === 0 && !showAllCrops
                  ? 'No cultivation data available'
                  : 'Select Crop'}
              </option>

              {showAllCrops ? (
                allCropsList.map((c) => {
                  const hasHistory = validDistrictCrops.includes(c);
                  return (
                    <option key={c} value={c}>
                      {hasHistory ? c : `⚠️ ${c}`}
                    </option>
                  );
                })
              ) : (
                validDistrictCrops.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))
              )}
            </select>

            {/* Checkbox: Show all crops */}
            <div className="mt-2 flex items-center gap-2">
              <input
                id="show-all-crops"
                type="checkbox"
                checked={showAllCrops}
                onChange={(e) => setShowAllCrops(e.target.checked)}
                className="w-4 h-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500/20 cursor-pointer"
              />
              <label
                htmlFor="show-all-crops"
                className="text-xs text-slate-600 select-none cursor-pointer hover:text-slate-900"
              >
                Show all crops (may use national averages)
              </label>
            </div>

            {/* Warning when selecting a cold-start crop */}
            {isColdStartCrop && (
              <div className="mt-2 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-1.5 shadow-2xs">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                <span className="leading-tight font-medium">
                  ⚠️ No historical data for {selectedCrop} in {selectedDistrict}. Prediction will use national {selectedCrop} averages and may be less accurate.
                </span>
              </div>
            )}

            {/* District with 0 crops message */}
            {!showAllCrops && validDistrictCrops.length === 0 && selectedDistrict && (
              <p className="text-slate-500 text-[11px] mt-1.5 italic">
                No cultivation data available for {selectedDistrict}.
              </p>
            )}

            {errors.crop && (
              <p className="text-rose-600 text-[11px] mt-1 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.crop.message}
              </p>
            )}
          </div>
        </div>

        {/* Season & Irrigation Type (Filtered by Crop + District) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Cultivation Season */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Cultivation Season <span className="text-emerald-600">*</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(['Maha', 'Yala'] as const).map((s) => {
                const isAvailable = availableSeasons.includes(s as any);
                const isSelected = selectedSeason === s;
                return (
                  <label
                    key={s}
                    className={`flex items-center justify-center gap-2 px-3 py-2 rounded-xl border text-xs font-medium cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-800 font-semibold shadow-xs'
                        : isAvailable
                        ? 'border-slate-200 text-slate-600 hover:bg-slate-50'
                        : 'border-slate-200 bg-slate-100 text-slate-400 opacity-60 cursor-not-allowed'
                    }`}
                  >
                    <input
                      type="radio"
                      value={s}
                      disabled={!isAvailable && availableSeasons.length > 0}
                      {...register('season')}
                      className="sr-only"
                    />
                    <span>{s === 'Maha' ? 'Maha (Major)' : 'Yala (Minor)'}</span>
                  </label>
                );
              })}
            </div>
            {errors.season && (
              <p className="text-rose-600 text-[11px] mt-1">{errors.season.message}</p>
            )}
          </div>

          {/* Irrigation Type */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Water / Irrigation Regime <span className="text-emerald-600">*</span>
            </label>
            <select
              {...register('irrigation_type')}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm bg-white focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all"
            >
              {availableIrrigation.map((irr) => (
                <option key={irr} value={irr}>
                  {irr === 'Irrigated'
                    ? 'Irrigated (Major/Minor Tanks)'
                    : irr === 'Rainfed'
                    ? 'Rainfed'
                    : 'Unspecified / Combined'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Spot USD/LKR Rate (Auto-populated with helper text) */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <DollarSign className="w-3.5 h-3.5 text-emerald-600" />
              <span>USD / LKR Exchange Rate Assumption</span>
            </span>
            <span className="text-[11px] text-slate-400 font-normal font-mono">
              Default: {defaultUsdRate}
            </span>
          </label>
          <input
            type="number"
            step="0.01"
            min={50}
            max={1000}
            {...register('usd_lkr_rate', { valueAsNumber: true })}
            className={`w-full px-3.5 py-2.5 rounded-xl border text-sm font-mono focus:outline-none focus:ring-2 transition-all ${
              errors.usd_lkr_rate
                ? 'border-rose-300 focus:ring-rose-500/20'
                : 'border-slate-300 focus:border-emerald-500 focus:ring-emerald-500/20'
            }`}
            placeholder="300.73"
          />
          <p className="text-[11px] text-slate-500 mt-1.5">
            Latest known rate. Override with current spot rate if you have it.
          </p>
          {errors.usd_lkr_rate && (
            <p className="text-rose-600 text-[11px] mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {errors.usd_lkr_rate.message}
            </p>
          )}
        </div>

        {/* Previous Season Cost */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <History className="w-3.5 h-3.5 text-emerald-600" />
              <span>Prior Season Cultivation Cost (LKR / Acre)</span>
            </span>
            {isAutoFilledMatch && (
              <span className="text-[11px] text-emerald-700 font-medium">
                Auto-populated
              </span>
            )}
          </label>
          <input
            type="number"
            step="any"
            min={0}
            {...register('prev_season_cost', {
              valueAsNumber: false,
            })}
            className={`w-full px-3.5 py-2.5 rounded-xl border text-sm font-mono focus:outline-none focus:ring-2 transition-all ${
              errors.prev_season_cost
                ? 'border-rose-300 focus:ring-rose-500/20'
                : 'border-slate-300 focus:border-emerald-500 focus:ring-emerald-500/20'
            }`}
            placeholder="e.g. 145000"
          />
          {errors.prev_season_cost ? (
            <p className="text-rose-600 text-[11px] mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {errors.prev_season_cost.message}
            </p>
          ) : isCostEmpty ? (
            <p className="text-[11px] text-slate-500 mt-1.5 flex items-center gap-1">
              <span>No prior season on record. Prediction will use the crop-level median. Leave blank if unknown.</span>
            </p>
          ) : isAutoFilledMatch ? (
            <p className="text-[11px] text-emerald-700 mt-1.5 flex items-center gap-1">
              <span>Auto-filled from {referenceYear} survey data (Rs {autoFilledCost.toLocaleString()}). Override if you have more recent numbers.</span>
            </p>
          ) : (
            <p className="text-[11px] text-slate-500 mt-1.5 flex items-center gap-1">
              <span>Custom prior cost specified (Rs {Number(watchedCost).toLocaleString()}). Leave blank if unknown.</span>
            </p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3.5 px-6 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm tracking-wide shadow-md shadow-emerald-700/20 hover:shadow-emerald-700/40 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 group cursor-pointer"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Generating Forward Prediction...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 text-emerald-200 group-hover:scale-110 transition-transform" />
              <span>Predict Cultivation Cost per Acre</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
};
