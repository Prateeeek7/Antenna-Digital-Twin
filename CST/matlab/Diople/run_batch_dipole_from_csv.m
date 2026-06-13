function run_batch_dipole_from_csv()
    % RUN_BATCH_DIPOLE_FROM_CSV
    % Batch-simulate dipole antennas from a CSV file.
    %
    % Expected CSV columns (one row per design):
    %   id, length_m, width_m, f0_Hz
    %
    % For each row this script:
    %   - builds a dipole antenna
    %   - sweeps S11 around f0
    %   - computes 3D radiation pattern at f0
    %   - computes E/H plane cuts
    %   - exports CSVs to an exports_matlab/ subfolder

    %% --- USER CONFIG ----------------------------------------------------
    csvFileName = 'dipole_designs_2p4GHz_10.csv';
    outDirName  = 'exports_matlab';

    % S11 sweep: +/- 20% around f0
    fSpanFactor = 0.2;
    nFreqPts    = 201;

    % 3D far-field sampling grid (degrees)
    thetaVec3D  = 0:5:180;
    phiVec3D    = 0:5:360;

    % 2D cuts
    phiEplane   = 0;
    thetaHplane = 90;

    %% --- DERIVED PATHS --------------------------------------------------
    csvPath = fullfile(pwd, csvFileName);
    outDir  = fullfile(pwd, outDirName);

    if ~isfile(csvPath)
        error('CSV file not found at: %s', csvPath);
    end

    if ~exist(outDir, 'dir')
        mkdir(outDir);
    end

    %% --- LOAD PARAMETER TABLE -------------------------------------------
    paramsTbl = readtable(csvPath);
    nDesigns  = height(paramsTbl);

    fprintf('Loaded %d dipole designs from %s\n', nDesigns, csvPath);

    %% --- MAIN LOOP OVER DESIGNS -----------------------------------------
    for k = 1:nDesigns
        id        = paramsTbl.id(k);
        length_m  = paramsTbl.length_m(k);
        width_m   = paramsTbl.width_m(k);
        f0_Hz     = paramsTbl.f0_Hz(k);

        if isnumeric(id)
            idStr = sprintf('id%g', id);
        else
            idStr = char(id);
        end

        fprintf('\n=== %d/%d: %s, f0 = %.3f GHz ===\n', ...
            k, nDesigns, idStr, f0_Hz / 1e9);
        fprintf('  length = %.3f mm, width = %.3f mm\n', ...
            length_m * 1e3, width_m * 1e3);

        %% --- BUILD ANTENNA GEOMETRY ------------------------------------
        ant = dipole;
        ant.Length = length_m;
        ant.Width  = width_m;

        %% --- S11 SWEEP --------------------------------------------------
        fmin = (1 - fSpanFactor) * f0_Hz;
        fmax = (1 + fSpanFactor) * f0_Hz;
        freq = linspace(fmin, fmax, nFreqPts);

        Z0   = 50;
        S    = sparameters(ant, freq, Z0);
        s11  = rfparam(S, 1, 1);

        S11_dB   = 20 * log10(abs(s11));
        S11_real = real(s11);
        S11_imag = imag(s11);

        S11Tbl = table(freq(:), S11_dB(:), S11_real(:), S11_imag(:), ...
            'VariableNames', {'freq_Hz', 'S11_dB', 'S11_real', 'S11_imag'});

        s11File = fullfile(outDir, sprintf('%s_S11.csv', idStr));
        writetable(S11Tbl, s11File);
        fprintf('  Saved S11 -> %s\n', s11File);

        %% --- 3D FAR-FIELD PATTERN --------------------------------------
        [g3D_dB, thetaGrid, phiGrid] = pattern(ant, f0_Hz, thetaVec3D, phiVec3D);
        [TH, PH] = meshgrid(thetaGrid, phiGrid);
        Far3DTbl = table(TH(:), PH(:), g3D_dB(:), ...
            'VariableNames', {'theta_deg', 'phi_deg', 'gain_dBi'});

        far3DFile = fullfile(outDir, sprintf('%s_farfield3D_f0.csv', idStr));
        writetable(Far3DTbl, far3DFile);
        fprintf('  Saved 3D far-field -> %s\n', far3DFile);

        %% --- 2D E-PLANE CUT --------------------------------------------
        [gE_dB, thetaE] = pattern(ant, f0_Hz, thetaVec3D, phiEplane);
        EplaneTbl = table(thetaE(:), gE_dB(:), ...
            'VariableNames', {'theta_deg', 'gain_dBi'});

        eplaneFile = fullfile(outDir, ...
            sprintf('%s_Eplane_f0_phi%d.csv', idStr, round(phiEplane)));
        writetable(EplaneTbl, eplaneFile);
        fprintf('  Saved E-plane -> %s\n', eplaneFile);

        %% --- 2D H-PLANE CUT --------------------------------------------
        [gH_dB, phiH] = pattern(ant, f0_Hz, phiVec3D, thetaHplane);
        HplaneTbl = table(phiH(:), gH_dB(:), ...
            'VariableNames', {'phi_deg', 'gain_dBi'});

        hplaneFile = fullfile(outDir, ...
            sprintf('%s_Hplane_f0_theta%d.csv', idStr, round(thetaHplane)));
        writetable(HplaneTbl, hplaneFile);
        fprintf('  Saved H-plane -> %s\n', hplaneFile);
    end

    fprintf('\nAll dipole designs finished. Results in folder: %s\n', outDir);
end
