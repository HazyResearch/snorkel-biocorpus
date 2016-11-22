import sys

# python split_pubtator_file.py FPATH NDOCS MAXNS
# Splits a PubTator file into MAXNS splits of NDOCS each
if __name__ == '__main__':
    try:
        fp = sys.argv[1]
        nd = int(sys.argv[2])
        ns = int(sys.argv[3])
    except:
        print "USAGE: python split_pubtator_file.py FPATH NDOCS_PER_SPLIT MAX_SPLITS"
        sys.exit(1)

    with open(fp, 'rb') as f:
        s     = 0
        d     = 0
        f_out = open(fp + '.split_%s_%s' % (nd, s), 'wb')
        for line in f:
            f_out.write(line)
            if len(line.strip()) == 0:
                d += 1
                if d % nd == 0:
                    f_out.close()
                    if s < ns:
                        f_out = open(fp + '.split_%s_%s' % (nd, s), 'wb')
                        s    += 1
                    else:
                        sys.exit(0)
        f_out.close()
