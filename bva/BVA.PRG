**************************************************************
*       Program : bva  (bar code vocalization)               *
*        Author : Alan Dechert                               *
*                 adechert@earthlink.net                     *
*                 916-791-0456  USA                          *
*      Language : xBase -- dBASE IV DOS dBASE 5.0 DOS FoxPro *
*       Purpose : Part of EVM2003 open voting system demo;   *
*                 this illustrates how a decimal number      *
*                 representing ballot selections can be      *
*                 interpreted, and the corresponding sound   *
*                 files played so that the voter can verify  *
*                 selections by listening to them read back. *
*          Date : 29 SEP 03                                  *
*         NOTES : (1) Compiled at the command line with      *
*                    dBASE 5.0 for DOS:  BDL bvm -Cconfig -L *
*                 (2) Most of the code here is to work       *
*                     around the fact that dBASE doesn't     *
*                     have built-in support for long         *
*                     integers.  The long integer -- as many *
*                     as 35 decimal digits -- is intended to *
*                     be read from a barcode scanner.  The   *
*                     decimal integer is chopped in two with *
*                     the following in mind: long integer =  *
*                       first part X 10^18 + second part     *
*                     To get the long string of binary we    *
*                     convert the first part to binary and   *
*                     multiply by a binary representation of *
*                     10^18 (one quintillion).  Then we add  *
*                     that with the binary representation of *
*                     the second part.                       *
*                 (3) BVA.EXE distributed with the template  *
*                     table and a free wav file player for   *
*                     Windows by WebGeek, Inc.               *
*                     (dave@basicguru.com) and wav files     *
*                     specific to the demo.                  *
**************************************************************
PROCEDURE bva
   parameters mplayer
   set talk off
   set escape on
   set safety off
   set precision to 20
   on escape quit
   declare wavs[25]
   TooManyCats = .f.
   nwavs = 0
   * one quintillion binary representation:
   quint =  "00000000000000000000000000000000000000000000000000000000110111100000101101101011001110100111011001000000000000000000"
   
   barcodedata = space(42)
   
   clear
   @12,12 say "NO READ"
   @13,12 get barcodedata
   READ
   
   barcodedata = rtrim(ltrim(barcodedata))
   if val(barcodedata) = 0 .or. len(barcodedata) <> 40
      clear
      wait "Invalid input... please try again"
      quit
   endif
   
   ballot = left(barcodedata,4)
   selstring = substr(barcodedata,5)

   dhandle = fcreate("test-str.txt")
   lvoid = fputs(dhandle,barcodedata)
   lvoid = fputs(dhandle,ballot)
   lvoid = fputs(dhandle,selstring)

   selstring = revert(ballot,selstring)

   lvoid = fputs(dhandle,selstring)
   
   @12,12 say "READING"
   
   len1 = len(selstring)
   cdec1 = left(selstring,len1-18)
   cdec2 = right(selstring,18)
   
   dec1 = val(cdec1)
   dec2 = val(cdec2)
   
   * convert dec1 to a string of binary digits (called bin1)
   bin1 = ""
   do while dec1 > 0
      bin1 = iif(mod(dec1,2) = 1,"1","0") + bin1
      dec1 = int(dec1/2)
   enddo
   
   ** convert dec2 to string of binary digits
   bin2 = ""
   do while dec2 > 0
      bin2 = iif(mod(dec2,2) = 1,"1","0") + bin2
      dec2 = int(dec2/2)
   enddo
   
   *** pad bin1 with zeros
   n = len(bin1)
   do while n < 116
      bin1 = "0" + bin1
      n = n + 1
   enddo
   
   declare mtable[63,116]
   
   for n = 1 to 116
      mtable[1,n] = val(substr(quint,n,1))
      mtable[2,n] = val(substr(bin1,n,1))
   next
   for n = 3 to 63
      for m = 1 to 116
         mtable[n,m] = 0
      next
   next
   
   ** long multiplication of bin1 times 10^18
   n = 0
   nrow = 2
   q2 = quint
   do while nrow <= 61
      nrow = nrow + 1
      if substr(bin1,len(bin1) - n,1) = "1"
         cntr = 0
         m = 2
         do while m >= 2
            m = len(q2) - cntr
            mtable[nrow,m] = val(substr(q2,m,1))
            cntr = cntr + 1
         enddo
      else
         cntr = 0
         m = 1
         do while m >= 1
            m = len(q2) - cntr
            if m <> 0 
               mtable[nrow,m] = 0
            endif
            cntr = cntr + 1
         enddo
      endif
      q2 = substr(q2,2)
      n = n + 1
   enddo
   
   * pad bin2 with zeros
   n = len(bin2)
   do while n < 116
      bin2 = "0" + bin2
      n = n + 1
   enddo
   
   nrow = nrow + 1
   
   ** enter a row with bin2
   for n = 1 to 116
      mtable[nrow,n] = val(substr(bin2,n,1))
   next
   
   ** initialize array (bval) with zeros
   declare bval[116]
   
   for n = 1 to 116
      bval[n] = 0
   next
   
   ** go to the 3rd row 
   nrow = 3
   ** add the rows -- accumulate to bval.  Remember to carry the one!
   do while nrow <= 63
      n = 116
      carry = 0
      do while n >= 1
         bval[n] = bval[n] + mtable[nrow,n] + carry
         do case
            case bval[n] = 2
               bval[n] = 0
               carry = 1
            case bval[n] = 3
               bval[n] = 1
               carry = 1
            otherwise
               carry = 0
         endcase
         n = n - 1
      enddo
      nrow = nrow + 1
   enddo
   nrow = nrow + 2
   
   ** Also build resultant string indicating ballot selections.
   
   StringOfSelections = ""
   for n = 1 to 116
      StringOfSelections = StringOfSelections + str(bval[n],1)
   next
   positiondata = "018 098 173 203 234 273 304 343 372 392 412"
   
   clear
   lvoid = fputs(dhandle,stringofselections)
   lvoid = fclose(dhandle)

   
   ** first eleven contests
   declare first11[11,5]
   nwavs = 0
   
   
   for n = 1 to 11
      first11[n,2] = val(substr(positiondata, n * 4 - 3,2))
      first11[n,3] = val(substr(positiondata, n * 4 - 1,1))
      first11[n,1] = at("1", substr(stringofselections,first11[n,2],first11[n,3]))
      first11[n,5] = at("1", substr(stringofselections,first11[n,2],first11[n,3]),2)
      if first11[n,1] = 0 
         first11[n,4] = "np" + iif(n < 10, "0" + str(n,1),str(n,2)) + ".wav"
      else
         if first11[n,1] + first11[n,2] < 11
            first11[n,4] = "sel00" + str(first11[n,1] + first11[n,2]-1,1) + ".wav"
         else
            first11[n,4] = "sel0" + str(first11[n,1] + first11[n,2]-1,2) + ".wav"
         endif
      endif
      nwavs = nwavs + 1
      wavs[n] = first11[n,4]
   next
   
   ** twelveth contest
   if "1" $ substr(StringOfSelections,43,10)
      if at("1", substr(stringofselections,43,10),4) <> 0
         TooManyCats = .t.
      endif
      char = rtrim(ltrim(str(at("1", substr(stringofselections,43,10))+42,2)))
      char = "0" + char
      wavs[12] = "sel&char" + ".wav"
      nwavs = nwavs + 1
      cat2 = at("1", substr(stringofselections,43,10),2)
      if cat2 > 0
         char = "0" + rtrim(ltrim(str(cat2 + 42)))
         wavs[13] = "sel&char" + ".wav"
         nwavs = nwavs + 1
         cat3 = at("1", substr(stringofselections,43,10),3)
         if cat3 > 0
            char = "0" + rtrim(ltrim(str(cat3 + 42)))
            wavs[14] = "sel&char" + ".wav"
            nwavs = nwavs + 1
         endif
      endif
   else
      wavs[12] = "np12.wav"
      nwavs = nwavs + 1 
   endif
   checkno = nwavs

   ** thirteenth contest
   declare commiss[8,5]
   for n = 1 to 8
      commiss[n,2] = 45 + (8 * n)
      commiss[n,3] = 52 + (8 * n)
      commiss[n,1] = at("1", substr(stringofselections,commiss[n,2],8))
      commiss[n,5] = at("1", substr(stringofselections,commiss[n,2],8),2)
      if commiss[n,1] = 0 
         commiss[n,4] = " "
      else
         if commiss[n,1] + commiss[n,2] < 101
            commiss[n,4] = "sel0" + str(commiss[n,1] + commiss[n,2]-1,2) + ".wav"
         else
            commiss[n,4] = "sel" + str(commiss[n,1] + commiss[n,2]-1,3) + ".wav"
         endif
         nwavs = nwavs + 1
         wavs[nwavs] = commiss[n,4]
      endif
   next
   if nwavs = checkno
      nwavs = nwavs + 1
      wavs[nwavs] = "np" + str(13,2) + ".wav"
   else
      dont_care = asort(commiss,1,-1,1)
      for i = 1 to (nwavs - checkno)
         wavs[nwavs + 1 -i] = commiss[i,4]
      next
   endif
   
   testval = 0
   for i = 1 to 11
      testval = testval + first11[i,5]
   next
   for i = 1 to 8
      testval = testval + commiss[i,5]
   next
   
   if testval <> 0 .or. TooManyCats
      clear
      wait "Invalid input... please try again"
      quit
   endif
   
   do playlist with mplayer
RETURN   

PROCEDURE playlist
   parameters mplay

   n = fcreate("bvalist.asx")
   x = fputs(n,[<Asx Version = "3.0" >])
   x = fputs(n," ")
   x = fputs(n,[<Param Name = "Name" Value = "BVALIST" />])
   x = fputs(n," ")
   x = fputs(n,[<Param Name = "PlaylistAttribute" Value = "0" />])
   x = fputs(n," ")
   x = fputs(n,[<Param Name = "AllowShuffle" Value = "no" />])
   x = fputs(n," ")
   
   for i = 1 to nwavs
      x = fputs(n,[<Entry>])
      x = fputs(n," ")
      x = fputs(n,"<Title> File " + str(i,2) + " </Title>")
      x = fputs(n," ")
      x = fputs(n,[<Ref href = "] + wavs[i] + ["/>])
      x = fputs(n," ")
      x = fputs(n,[</Entry>])
      x = fputs(n," ")
   next
   
   x = fputs(n,[</Asx>])
   x = fputs(n," ")
   x = fputs(n," ")
   lvoid = fclose(n)

   if type("mplay") = "L"
      for n = 1 to nwavs
         run wav &wavs[n]>>nul
      next
   else
      mplay = rtrim(ltrim(mplay))
      if upper(mplay) = "MP"
        mplay = "c:\progra~1\window~1\wmplayer.exe"
      endif
      if file("&mplay")
         ctest = mplay + " /play bvalist.asx"
         run &ctest
      else
         wait "can't find wmplayer ... quitting!"
         quit
      endif
   endif
   use
RETURN
   
********************
function revert
********************
parameters key, num

declare keydigits[4]
declare numdigits[len(num)]
for i = 1 to 4
   keydigits[i] = substr(key,i,1)
next
for i = 1 to len(num)
   numdigits[i] = substr(num,i,1)
next
for i = 1 to len(num)
   numdigits[i] = str(mod(val(numdigits[i]) - val(keydigits[iif(mod(i,4)=0,4,mod(i,4))]),10),1)
next
retval = ""
for i = 1 to len(num)
   retval = retval + numdigits[i]
next
return retval

