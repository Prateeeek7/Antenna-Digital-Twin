function run_batch_patch_from_csv()
    % RUN_BATCH_PATCH_FROM_CSV
    % Batch-simulate rectangular microstrip patch antennas from a CSV file.
    %
    % Expected CSV columns (one row per design):
    %   id, L, W, h, feed_x, feed_y, eps_r, tan_delta, f0_Hz
    %   - L, W, h, feed_x, feed_y in metres
    %   - f0_Hz in Hz
    %
    % For each row this script:
    %   - builds a patchMicrostrip antenna
    %   - sweeps S11 around f0
    %   - computes 3D radiation pattern at f0
    %   - computes 2D E-plane (phi = 0) and H-plane (theta = 90) cuts
    %   - exports CSVs to an exports_matlab/ subfolder
    %
    % Usage (Desktop MATLAB):
    %   1) Set your current folder to the one containing the CSV
    %      (e.g. Antenna Digital Twin/CST).
    %   2) Make sure this file is on the MATLAB path or in the same folder.
    %   3) In the Command Window, run:
    %           run_batch_patch_from_csv
    %
    % Usage (MATLAB Online):
    %   1) Upload the CSV and this .m file into the same folder.
    %   2) Open this file in the editor and click Run, or call the function
    %      from the Command Window.

    %% --- USER CONFIG ----------------------------------------------------
    % Name of the CSV file in the *current* folder.
    csvFileName = 'cst_designs_2p4GHz_10.csv';

    % Name of the output folder (created as a subfolder of the current folder).
    outDirName  = 'exports_matlab';

    % S11 sweep: +/- 20% around f0
    fSpanFactor = 0.2;           % fraction of f0
    nFreqPts    = 201;           % number of frequency samples

    % 3D far-field sampling grid (in degrees)
    thetaVec3D  = 0:5:180;
    phiVec3D    = 0:5:360;

    % 2D cuts
    phiEplane   = 0;             % E-plane: fixed phi, sweep theta
    thetaHplane = 90;            % H-plane: fixed theta, sweep phi

    % Extra ground-plane margin around the patch (in metres)
    subMargin_m = 10e-3;         % 10 mm

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
    % Expected variables:
    %   id, L, W, h, feed_x, feed_y, eps_r, tan_delta, f0_Hz
    paramsTbl = readtable(csvPath);
    nDesigns  = height(paramsTbl);

    fprintf('Loaded %d designs from %s\n', nDesigns, csvPath);

    %% --- MAIN LOOP OVER DESIGNS -----------------------------------------
    for k = 1:nDesigns
        % Extract parameters for this design
        id        = paramsTbl.id(k);
        L_m       = paramsTbl.L(k);
        W_m       = paramsTbl.W(k);
        h_m       = paramsTbl.h(k);
        feed_x_m  = paramsTbl.feed_x(k);
        feed_y_m  = paramsTbl.feed_y(k);
        eps_r     = paramsTbl.eps_r(k);
        tan_delta = paramsTbl.tan_delta(k);
        f0_Hz     = paramsTbl.f0_Hz(k);

        % ID string for filenames
        if isnumeric(id)
            idStr = sprintf('id%g', id);
        else
            idStr = char(id);
        end

        fprintf('\n=== %d/%d: %s, f0 = %.3f GHz ===\n', ...
            k, nDesigns, idStr, f0_Hz / 1e9);
        fprintf('  L = %.3f mm, W = %.3f mm, h = %.3f mm\n', ...
            L_m * 1e3, W_m * 1e3, h_m * 1e3);
        fprintf('  feed_x = %.3f mm, feed_y = %.3f mm\n', ...
            feed_x_m * 1e3, feed_y_m * 1e3);
        fprintf('  eps_r = %.3f, tan_delta = %.4f\n', eps_r, tan_delta);

        %% --- BUILD ANTENNA GEOMETRY ------------------------------------
        ant = patchMicrostrip;      % base rectangular patch geometry

        % Basic dimensions (metres)
        ant.Length = L_m;
        ant.Width  = W_m;
        ant.Height = h_m;

        % Substrate (name-value syntax; no custom name needed)
        sub = dielectric('EpsilonR', eps_r, 'LossTangent', tan_delta);
        ant.Substrate = sub;

        % Ground plane dimensions (patch size + margin)
        ant.GroundPlaneLength = L_m + 2 * subMargin_m;
        ant.GroundPlaneWidth  = W_m + 2 * subMargin_m;

        % Feed offset (x, y) from patch centre.
        % MATLAB enforces |FeedOffset(2)| < Length/2 strictly. Use
        % a conservative limit (25% of patch length) so all designs are valid.
        maxY          = 0.25 * ant.Length;
        feed_y_clamped = min(max(feed_y_m, -maxY), maxY);
        if abs(feed_y_clamped - feed_y_m) > 1e-6
            fprintf('  Note: feed_y clamped from %.3f mm to %.3f mm\n', ...
                feed_y_m * 1e3, feed_y_clamped * 1e3);
        end
        ant.FeedOffset = [feed_x_m, feed_y_clamped];

        %% --- S11 SWEEP --------------------------------------------------
        fmin = (1 - fSpanFactor) * f0_Hz;
        fmax = (1 + fSpanFactor) * f0_Hz;
        freq = linspace(fmin, fmax, nFreqPts);

        Z0   = 50;                      % reference impedance
        S    = sparameters(ant, freq, Z0);
        s11  = rfparam(S, 1, 1);        % complex S11

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
        % g3D_dB is size [numel(phiGrid) x numel(thetaGrid)]

        [TH, PH] = meshgrid(thetaGrid, phiGrid);
        Far3DTbl = table(TH(:), PH(:), g3D_dB(:), ...
            'VariableNames', {'theta_deg', 'phi_deg', 'gain_dBi'});

        far3DFile = fullfile(outDir, sprintf('%s_farfield3D_f0.csv', idStr));
        writetable(Far3DTbl, far3DFile);
        fprintf('  Saved 3D far-field -> %s\n', far3DFile);

        %% --- 2D E-PLANE CUT (phi fixed, theta sweep) -------------------
        [gE_dB, thetaE] = pattern(ant, f0_Hz, thetaVec3D, phiEplane);

        EplaneTbl = table(thetaE(:), gE_dB(:), ...
            'VariableNames', {'theta_deg', 'gain_dBi'});

        eplaneFile = fullfile(outDir, ...
            sprintf('%s_Eplane_f0_phi%d.csv', idStr, round(phiEplane)));
        writetable(EplaneTbl, eplaneFile);
        fprintf('  Saved E-plane -> %s\n', eplaneFile);

        %% --- 2D H-PLANE CUT (theta fixed, phi sweep) -------------------
        [gH_dB, phiH] = pattern(ant, f0_Hz, phiVec3D, thetaHplane);

        HplaneTbl = table(phiH(:), gH_dB(:), ...
            'VariableNames', {'phi_deg', 'gain_dBi'});

        hplaneFile = fullfile(outDir, ...
            sprintf('%s_Hplane_f0_theta%d.csv', idStr, round(thetaHplane)));
        writetable(HplaneTbl, hplaneFile);
        fprintf('  Saved H-plane -> %s\n', hplaneFile);
    end

    fprintf('\nAll designs finished. Results in folder: %s\n', outDir);
end

